from __future__ import annotations

import tempfile
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, send_file, session, url_for

from . import storage
from .pdfs import (
    budget_filename,
    build_budget_pdf,
    build_occurrence_pdf,
    build_stock_report_pdf,
    occurrence_filename,
    stock_report_filename,
)

bp = Blueprint("web", __name__)


def _safe_next(default: str = "web.dashboard") -> str:
    next_url = request.args.get("next") or request.form.get("next")
    if not next_url:
        return url_for(default)
    parsed = urlparse(next_url)
    if next_url.startswith("/") and not next_url.startswith("//") and not parsed.scheme and not parsed.netloc:
        return next_url
    return url_for(default)


@bp.after_app_request
def close_connection(response):
    storage.close_db()
    return response


@bp.before_app_request
def require_login():
    endpoint = request.endpoint or ""
    if endpoint == "static" or endpoint in {"web.login", "web.logout", "web.brand_image"}:
        return None
    if not storage.has_users():
        return redirect(url_for("web.login", next=request.path))
    if not session.get("user_id"):
        return redirect(url_for("web.login", next=request.path))
    return None


@bp.route("/login", methods=["GET", "POST"])
def login():
    setup_mode = not storage.has_users()
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        try:
            if setup_mode:
                confirm = request.form.get("confirm_password", "")
                if password != confirm:
                    raise ValueError("As passwords não coincidem.")
                user_id = storage.create_user(username, password)
                session.clear()
                session["user_id"] = user_id
                session["username"] = username.strip()
                flash("Primeiro utilizador criado com sucesso.", "success")
                return redirect(_safe_next())
            user = storage.verify_user(username, password)
            if not user:
                raise ValueError("Utilizador ou password inválido.")
            session.clear()
            session["user_id"] = int(user["id"])
            session["username"] = user["username"]
            return redirect(_safe_next())
        except ValueError as exc:
            flash(str(exc), "error")
    return render_template("login.html", setup_mode=setup_mode, next_url=request.args.get("next", ""))


@bp.get("/logout")
def logout():
    session.clear()
    flash("Sessão terminada.", "success")
    return redirect(url_for("web.login"))


@bp.get("/marca/imagem")
def brand_image():
    logo = storage.get_brand_logo()
    if not logo:
        abort(404)
    return send_file(
        BytesIO(logo["dados"]),
        mimetype=logo["content_type"],
        download_name=logo["filename"],
        max_age=300,
    )


@bp.get("/")
def index():
    return redirect(url_for("web.dashboard"))


@bp.get("/painel")
def dashboard():
    return render_template("dashboard.html", data=storage.dashboard_data())


@bp.route("/clientes", methods=["GET", "POST"])
def clientes():
    if request.method == "POST":
        try:
            storage.add_client(
                request.form.get("nome", ""),
                request.form.get("morada", ""),
                request.form.get("contacto", ""),
            )
            flash("Cliente guardado com sucesso.", "success")
        except ValueError as exc:
            flash(str(exc), "error")
        return redirect(url_for("web.clientes"))
    termo = request.args.get("q", "")
    return render_template("clientes.html", clientes=storage.list_clients(termo), termo=termo)


@bp.route("/clientes/<int:client_id>/editar", methods=["GET", "POST"])
def editar_cliente(client_id: int):
    # route name intentionally descriptive; we'll redirect/render clients with editing context
    client = storage.get_client(client_id)
    if not client:
        flash("Cliente não encontrado.", "error")
        return redirect(url_for("web.clientes"))

    if request.method == "POST":
        try:
            storage.update_client(
                client_id,
                request.form.get("nome", ""),
                request.form.get("morada", ""),
                request.form.get("contacto", ""),
            )
            flash("Cliente atualizado com sucesso.", "success")
            return redirect(url_for("web.clientes"))
        except ValueError as exc:
            flash(str(exc), "error")

    termo = request.args.get("q", "")
    return render_template(
        "clientes.html",
        clientes=storage.list_clients(termo),
        termo=termo,
        editing=True,
        client=client,
    )


@bp.post("/clientes/<int:client_id>/eliminar")
def eliminar_cliente(client_id: int):
    storage.delete_client(client_id)
    flash("Cliente eliminado.", "success")
    return redirect(url_for("web.clientes"))


@bp.route("/ocorrencias", methods=["GET", "POST"])
def ocorrencias():
    if request.method == "POST":
        try:
            storage.add_occurrence(int(request.form.get("cliente_id", "0")), request.form.get("descricao", ""))
            flash("Ocorrência registada.", "success")
        except (TypeError, ValueError) as exc:
            flash(str(exc), "error")
        return redirect(url_for("web.ocorrencias"))
    client_id = request.args.get("cliente_id", type=int)
    return render_template(
        "ocorrencias.html",
        clientes=storage.list_clients(),
        ocorrencias=storage.list_occurrences(client_id),
        cliente_id=client_id,
    )


@bp.get("/ocorrencias/<int:occurrence_id>/pdf")
def ocorrencia_pdf(occurrence_id: int):
    occurrence = storage.get_occurrence(occurrence_id)
    if not occurrence:
        flash("Ocorrência não encontrada.", "error")
        return redirect(url_for("web.ocorrencias"))
    pdf_bytes = build_occurrence_pdf(
        occurrence,
        storage.get_brand_logo(),
        storage.get_store_profile(),
    )
    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=occurrence_filename(occurrence),
    )


def _parse_budget_materials() -> list[dict[str, int]]:
    material_ids = request.form.getlist("material_id")
    quantities = request.form.getlist("material_qty")
    items: list[dict[str, int]] = []
    for material_id, quantity in zip(material_ids, quantities):
        if not material_id or not quantity:
            continue
        items.append({"stock_id": int(material_id), "quantidade": int(quantity)})
    return items


@bp.route("/orcamentos", methods=["GET", "POST"])
def orcamentos():
    if request.method == "POST":
        try:
            storage.create_budget(
                int(request.form.get("cliente_id", "0")),
                request.form.get("descricao", ""),
                float(request.form.get("preco", "0").replace(",", ".")),
                request.form.get("include_iva") == "on",
                float((request.form.get("valor_pago", "0") or "0").replace(",", ".")),
                _parse_budget_materials(),
            )
            flash("Orçamento criado e stock atualizado.", "success")
        except (TypeError, ValueError) as exc:
            flash(str(exc), "error")
        return redirect(url_for("web.orcamentos"))
    client_id = request.args.get("cliente_id", type=int)
    budgets = storage.list_budgets(client_id)
    return render_template(
        "orcamentos.html",
        clientes=storage.list_clients(),
        materiais=storage.list_stock(),
        orcamentos=budgets,
        consumos=storage.list_budget_materials_for_budgets([int(row["id"]) for row in budgets]),
        cliente_id=client_id,
    )


@bp.route("/orcamentos/<int:budget_id>/editar", methods=["GET", "POST"])
def editar_orcamento(budget_id: int):
    budget = storage.get_budget(budget_id)
    if not budget:
        flash("Orçamento não encontrado.", "error")
        return redirect(url_for("web.orcamentos"))

    if request.method == "POST":
        try:
            storage.update_budget(
                budget_id,
                int(request.form.get("cliente_id", "0")),
                request.form.get("descricao", ""),
                float(request.form.get("preco", "0").replace(",", ".")),
                request.form.get("include_iva") == "on",
                float((request.form.get("valor_pago", "0") or "0").replace(",", ".")),
                _parse_budget_materials(),
            )
            flash("Orçamento atualizado com sucesso.", "success")
            return redirect(url_for("web.orcamentos"))
        except (TypeError, ValueError) as exc:
            flash(str(exc), "error")

    client_id = request.args.get("cliente_id", type=int)
    budgets = storage.list_budgets(client_id)
    return render_template(
        "orcamentos.html",
        clientes=storage.list_clients(),
        materiais=storage.list_stock(),
        orcamentos=budgets,
        consumos=storage.list_budget_materials_for_budgets([int(row["id"]) for row in budgets]),
        cliente_id=client_id,
        editing=True,
        budget=budget,
        selected_materials=storage.list_budget_materials(budget_id),
    )


@bp.post("/orcamentos/<int:budget_id>/eliminar")
def eliminar_orcamento(budget_id: int):
    restored = storage.delete_budget(budget_id)
    if restored:
        flash(f"Orçamento eliminado e {restored} unidade(s) repostas no stock.", "success")
    else:
        flash("Orçamento eliminado.", "success")
    return redirect(url_for("web.orcamentos"))


@bp.get("/orcamentos/<int:budget_id>/pdf")
def orcamento_pdf(budget_id: int):
    budget = storage.get_budget(budget_id)
    if not budget:
        flash("Orçamento não encontrado.", "error")
        return redirect(url_for("web.orcamentos"))
    cliente = storage.get_client(budget["cliente_id"])
    pdf_bytes = build_budget_pdf(
        cliente,
        budget,
        storage.list_budget_materials(budget_id),
        storage.get_brand_logo(),
        storage.get_store_profile(),
    )
    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=budget_filename(budget),
    )


@bp.get("/pesquisa")
def pesquisa():
    termo = request.args.get("q", "")
    clientes = storage.list_clients(termo) if termo else []
    materiais = storage.list_stock(termo) if termo else []
    historico = {}
    for cliente in clientes:
        historico[cliente["id"]] = {
            "ocorrencias": storage.list_occurrences(cliente["id"]),
            "orcamentos": storage.list_budgets(cliente["id"]),
        }
    return render_template(
        "pesquisa.html",
        termo=termo,
        clientes=clientes,
        materiais=materiais,
        historico=historico,
    )


@bp.route("/stock", methods=["GET", "POST"])
def stock():
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "add":
                storage.add_stock(
                    request.form.get("nome", ""),
                    request.form.get("categoria", ""),
                    int(request.form.get("quantidade", "0") or 0),
                    int(request.form.get("stock_minimo", "0") or 0),
                    request.form.get("localizacao", ""),
                    request.form.get("notas", ""),
                )
                flash("Produto adicionado ao stock.", "success")
            elif action == "quantity":
                storage.update_stock_quantity(
                    int(request.form.get("material_id", "0")),
                    int(request.form.get("quantidade", "0") or 0),
                )
                flash("Quantidade atualizada.", "success")
            elif action == "delta":
                storage.increment_stock_quantity(
                    int(request.form.get("material_id", "0")),
                    int(request.form.get("delta", "0") or 0),
                )
                flash("Stock atualizado.", "success")
            elif action == "delete":
                storage.delete_stock(int(request.form.get("material_id", "0")))
                flash("Material eliminado.", "success")
        except (TypeError, ValueError) as exc:
            flash(str(exc), "error")
        return redirect(url_for("web.stock"))
    termo = request.args.get("q", "")
    low_only = request.args.get("low") == "1"
    return render_template("stock.html", materiais=storage.list_stock(termo, low_only), termo=termo, low_only=low_only)


@bp.get("/stock/pdf")
def stock_pdf():
    low_only = request.args.get("tipo") == "reposicao" or request.args.get("low") == "1"
    materiais = storage.list_stock("", low_only)
    pdf_bytes = build_stock_report_pdf(
        materiais,
        low_only,
        storage.get_brand_logo(),
        storage.get_store_profile(),
    )
    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=stock_report_filename(low_only),
    )


def _backup_file(filename: str) -> Path:
    safe_name = Path(filename).name
    if safe_name != filename or not safe_name.lower().endswith((".db", ".sqlite", ".sqlite3")):
        abort(404)
    path = Path(current_app.config["BACKUP_DIR"]) / safe_name
    if not path.exists() or not path.is_file():
        abort(404)
    return path


@bp.get("/manutencao/backups/<path:filename>/descarregar")
def descarregar_backup(filename: str):
    path = _backup_file(filename)
    return send_file(path, as_attachment=True, download_name=path.name)


@bp.post("/manutencao/backups/<path:filename>/eliminar")
def eliminar_backup(filename: str):
    path = _backup_file(filename)
    path.unlink()
    flash("Cópia de segurança eliminada.", "success")
    return redirect(url_for("web.manutencao"))


@bp.route("/manutencao", methods=["GET", "POST"])
def manutencao():
    backups = sorted(Path(current_app.config["BACKUP_DIR"]).glob("*.db"), reverse=True)
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "backup":
                backup = storage.create_backup()
                flash(f"Cópia de segurança criada: {backup.name}", "success")
            elif action == "restore":
                file = request.files.get("backup_file")
                if not file or not file.filename:
                    raise ValueError("Selecione um ficheiro .db.")
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
                tmp_path = Path(tmp.name)
                tmp.close()
                file.save(tmp_path)
                storage.restore_backup(tmp_path)
                tmp_path.unlink(missing_ok=True)
                flash("Cópia restaurada com sucesso.", "success")
            elif action == "reset":
                db_path = Path(current_app.config["DATABASE"])
                storage.close_db()
                db_path.unlink(missing_ok=True)
                storage.init_db()
                flash("Base de dados limpa.", "success")
            elif action == "brand_logo":
                storage.save_brand_logo(request.files.get("brand_logo"))
                flash("Imagem da marca atualizada com sucesso.", "success")
            elif action == "remove_brand_logo":
                storage.remove_brand_logo()
                flash("Imagem da marca removida.", "success")
            elif action == "store_profile":
                storage.save_store_profile(
                    request.form.get("store_name", ""),
                    request.form.get("store_subtitle", ""),
                    request.form.get("store_contact", ""),
                    request.form.get("store_address", ""),
                )
                flash("Dados da loja atualizados com sucesso.", "success")
        except (OSError, ValueError) as exc:
            flash(str(exc), "error")
        return redirect(url_for("web.manutencao"))
    return render_template("manutencao.html", backups=backups, store_profile=storage.get_store_profile())
