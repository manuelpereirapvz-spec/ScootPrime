from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import current_app, g
from werkzeug.security import check_password_hash, generate_password_hash

BRAND_LOGO_SETTING = "brand_logo_filename"
ALLOWED_BRAND_LOGO_EXTENSIONS = {".png", ".jpg", ".jpeg"}
STORE_PROFILE_DEFAULTS = {
    "store_name": "ScootPrime",
    "store_subtitle": "Servico de Reparacao",
    "store_contact": "Filipe - 937320683",
    "store_address": "",
}


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        conn = sqlite3.connect(current_app.config["DATABASE"])
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


def close_db(_: Exception | None = None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db() -> None:
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            morada TEXT,
            contacto TEXT
        );

        CREATE TABLE IF NOT EXISTS ocorrencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            data TEXT,
            descricao TEXT,
            FOREIGN KEY(cliente_id) REFERENCES clientes(id)
        );

        CREATE TABLE IF NOT EXISTS orcamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            data TEXT,
            descricao TEXT,
            preco REAL,
            iva REAL,
            total REAL,
            include_iva INTEGER DEFAULT 1,
            valor_pago REAL DEFAULT 0.0,
            FOREIGN KEY(cliente_id) REFERENCES clientes(id)
        );

        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT,
            quantidade INTEGER NOT NULL DEFAULT 0,
            stock_minimo INTEGER NOT NULL DEFAULT 0,
            localizacao TEXT,
            notas TEXT,
            atualizado_em TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS utilizadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            criado_em TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS orcamento_materiais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            orcamento_id INTEGER NOT NULL,
            stock_id INTEGER,
            nome_material TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            stock_antes INTEGER NOT NULL,
            stock_depois INTEGER NOT NULL,
            data TEXT NOT NULL,
            FOREIGN KEY(orcamento_id) REFERENCES orcamentos(id),
            FOREIGN KEY(stock_id) REFERENCES stock(id)
        );

        CREATE TABLE IF NOT EXISTS configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS marca_imagem (
            chave TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            content_type TEXT NOT NULL,
            dados BLOB NOT NULL,
            atualizado_em TEXT NOT NULL
        );
        """
    )

    columns = {row["name"] for row in db.execute("PRAGMA table_info(orcamentos)").fetchall()}
    if "include_iva" not in columns:
        db.execute("ALTER TABLE orcamentos ADD COLUMN include_iva INTEGER DEFAULT 1")
    if "valor_pago" not in columns:
        db.execute("ALTER TABLE orcamentos ADD COLUMN valor_pago REAL DEFAULT 0.0")
    db.commit()


def add_client(nome: str, morada: str = "", contacto: str = "") -> int:
    nome = nome.strip()
    if not nome:
        raise ValueError("O nome é obrigatório.")
    cur = get_db().execute(
        "INSERT INTO clientes (nome, morada, contacto) VALUES (?, ?, ?)",
        (nome, morada.strip(), contacto.strip()),
    )
    get_db().commit()
    return int(cur.lastrowid)


def get_setting(key: str) -> str | None:
    row = get_db().execute("SELECT valor FROM configuracoes WHERE chave = ?", (key,)).fetchone()
    return row["valor"] if row else None


def set_setting(key: str, value: str) -> None:
    get_db().execute(
        """
        INSERT INTO configuracoes (chave, valor)
        VALUES (?, ?)
        ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor
        """,
        (key, value),
    )
    get_db().commit()


def delete_setting(key: str) -> None:
    get_db().execute("DELETE FROM configuracoes WHERE chave = ?", (key,))
    get_db().commit()


def get_store_profile() -> dict[str, str]:
    profile = STORE_PROFILE_DEFAULTS.copy()
    rows = get_db().execute(
        "SELECT chave, valor FROM configuracoes WHERE chave IN (?, ?, ?, ?)",
        tuple(STORE_PROFILE_DEFAULTS.keys()),
    ).fetchall()
    for row in rows:
        profile[row["chave"]] = row["valor"]
    return profile


def save_store_profile(name: str, subtitle: str = "", contact: str = "", address: str = "") -> dict[str, str]:
    name = name.strip()
    if not name:
        raise ValueError("O nome da loja e obrigatorio.")
    profile = {
        "store_name": name,
        "store_subtitle": subtitle.strip() or STORE_PROFILE_DEFAULTS["store_subtitle"],
        "store_contact": contact.strip(),
        "store_address": address.strip(),
    }
    db = get_db()
    for key, value in profile.items():
        db.execute(
            """
            INSERT INTO configuracoes (chave, valor)
            VALUES (?, ?)
            ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor
            """,
            (key, value),
        )
    db.commit()
    return profile


def get_brand_logo_path() -> Path | None:
    filename = get_setting(BRAND_LOGO_SETTING)
    if not filename:
        return None
    path = Path(current_app.config["BRAND_DIR"]) / filename
    if not path.exists():
        return None
    return path


def get_brand_logo() -> sqlite3.Row | None:
    return get_db().execute(
        """
        SELECT chave, filename, content_type, dados, atualizado_em
        FROM marca_imagem
        WHERE chave = ?
        """,
        (BRAND_LOGO_SETTING,),
    ).fetchone()


def save_brand_logo(file_storage) -> Path:
    if not file_storage or not file_storage.filename:
        raise ValueError("Selecione uma imagem da marca.")

    extension = Path(file_storage.filename).suffix.lower()
    if extension not in ALLOWED_BRAND_LOGO_EXTENSIONS:
        raise ValueError("Use uma imagem PNG ou JPG.")

    data = file_storage.read()
    if not data:
        raise ValueError("A imagem escolhida esta vazia.")

    content_type = "image/png" if extension == ".png" else "image/jpeg"
    filename = f"brand_logo{extension}"
    get_db().execute(
        """
        INSERT INTO marca_imagem (chave, filename, content_type, dados, atualizado_em)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(chave) DO UPDATE SET
            filename = excluded.filename,
            content_type = excluded.content_type,
            dados = excluded.dados,
            atualizado_em = excluded.atualizado_em
        """,
        (BRAND_LOGO_SETTING, filename, content_type, data, datetime.now().strftime("%d/%m/%Y %H:%M")),
    )
    get_db().commit()

    brand_dir = Path(current_app.config["BRAND_DIR"])
    brand_dir.mkdir(parents=True, exist_ok=True)
    target = brand_dir / filename

    for old_file in brand_dir.glob("brand_logo.*"):
        if old_file != target:
            old_file.unlink(missing_ok=True)

    target.write_bytes(data)
    set_setting(BRAND_LOGO_SETTING, filename)
    return target


def remove_brand_logo() -> None:
    brand_dir = Path(current_app.config["BRAND_DIR"])
    for old_file in brand_dir.glob("brand_logo.*"):
        old_file.unlink(missing_ok=True)
    delete_setting(BRAND_LOGO_SETTING)
    get_db().execute("DELETE FROM marca_imagem WHERE chave = ?", (BRAND_LOGO_SETTING,))
    get_db().commit()


def update_client(client_id: int, nome: str, morada: str = "", contacto: str = "") -> int:
    nome = nome.strip()
    if not nome:
        raise ValueError("O nome é obrigatório.")
    db = get_db()
    if not get_client(client_id):
        raise ValueError("Cliente não encontrado.")
    db.execute(
        "UPDATE clientes SET nome = ?, morada = ?, contacto = ? WHERE id = ?",
        (nome, morada.strip(), contacto.strip(), client_id),
    )
    db.commit()
    return client_id


def has_users() -> bool:
    row = get_db().execute("SELECT COUNT(*) FROM utilizadores").fetchone()
    return bool(row and row[0])


def create_user(username: str, password: str) -> int:
    username = username.strip()
    if not username:
        raise ValueError("O utilizador é obrigatório.")
    if len(password) < 6:
        raise ValueError("A password deve ter pelo menos 6 caracteres.")
    try:
        cur = get_db().execute(
            "INSERT INTO utilizadores (username, password_hash, criado_em) VALUES (?, ?, ?)",
            (username, generate_password_hash(password), datetime.now().strftime("%d/%m/%Y %H:%M")),
        )
        get_db().commit()
        return int(cur.lastrowid)
    except sqlite3.IntegrityError:
        raise ValueError("O utilizador já existe.")


def verify_user(username: str, password: str) -> sqlite3.Row | None:
    user = get_db().execute(
        "SELECT id, username, password_hash FROM utilizadores WHERE username = ?",
        (username.strip(),),
    ).fetchone()
    if user and check_password_hash(user["password_hash"], password):
        return user
    return None


def get_user(user_id: int | None) -> sqlite3.Row | None:
    if not user_id:
        return None
    return get_db().execute(
        "SELECT id, username, criado_em FROM utilizadores WHERE id = ?",
        (user_id,),
    ).fetchone()


def change_user_password(user_id: int | None, current_password: str, new_password: str) -> None:
    if not user_id:
        raise ValueError("Sessão inválida.")

    user = get_db().execute(
        "SELECT id, password_hash FROM utilizadores WHERE id = ?",
        (user_id,),
    ).fetchone()
    if user is None:
        raise ValueError("Utilizador não encontrado.")
    if not check_password_hash(user["password_hash"], current_password):
        raise ValueError("A password atual está incorreta.")
    if len(new_password) < 6:
        raise ValueError("A nova password deve ter pelo menos 6 caracteres.")
    if check_password_hash(user["password_hash"], new_password):
        raise ValueError("A nova password deve ser diferente da atual.")

    get_db().execute(
        "UPDATE utilizadores SET password_hash = ? WHERE id = ?",
        (generate_password_hash(new_password), user_id),
    )
    get_db().commit()


def list_clients(term: str = "") -> list[sqlite3.Row]:
    return get_db().execute(
        """
        SELECT id, nome, morada, contacto
        FROM clientes
        WHERE nome LIKE ? OR contacto LIKE ? OR morada LIKE ?
        ORDER BY nome COLLATE NOCASE
        """,
        (f"%{term}%", f"%{term}%", f"%{term}%"),
    ).fetchall()


def get_client(client_id: int) -> sqlite3.Row | None:
    return get_db().execute(
        "SELECT id, nome, morada, contacto FROM clientes WHERE id = ?",
        (client_id,),
    ).fetchone()


def delete_client(client_id: int) -> None:
    db = get_db()
    db.execute("DELETE FROM ocorrencias WHERE cliente_id = ?", (client_id,))
    budget_ids = [row["id"] for row in db.execute("SELECT id FROM orcamentos WHERE cliente_id = ?", (client_id,)).fetchall()]
    for budget_id in budget_ids:
        _restore_budget_stock(db, budget_id)
        db.execute("DELETE FROM orcamento_materiais WHERE orcamento_id = ?", (budget_id,))
    db.execute("DELETE FROM orcamentos WHERE cliente_id = ?", (client_id,))
    db.execute("DELETE FROM clientes WHERE id = ?", (client_id,))
    db.commit()


def add_occurrence(client_id: int, descricao: str) -> int:
    if not get_client(client_id):
        raise ValueError("Cliente não encontrado.")
    descricao = descricao.strip()
    if not descricao:
        raise ValueError("A descrição é obrigatória.")
    cur = get_db().execute(
        "INSERT INTO ocorrencias (cliente_id, data, descricao) VALUES (?, ?, ?)",
        (client_id, datetime.now().strftime("%d/%m/%Y %H:%M"), descricao),
    )
    get_db().commit()
    return int(cur.lastrowid)


def list_occurrences(client_id: int | None = None) -> list[sqlite3.Row]:
    params: tuple[Any, ...] = ()
    where = ""
    if client_id:
        where = "WHERE o.cliente_id = ?"
        params = (client_id,)
    return get_db().execute(
        f"""
        SELECT o.id, o.cliente_id, o.data, o.descricao, c.nome AS cliente_nome
        FROM ocorrencias o
        LEFT JOIN clientes c ON c.id = o.cliente_id
        {where}
        ORDER BY o.id DESC
        """,
        params,
    ).fetchall()


def get_occurrence(occurrence_id: int) -> sqlite3.Row | None:
    return get_db().execute(
        """
        SELECT o.id, o.cliente_id, o.data, o.descricao, c.nome AS cliente_nome, c.morada, c.contacto
        FROM ocorrencias o
        LEFT JOIN clientes c ON c.id = o.cliente_id
        WHERE o.id = ?
        """,
        (occurrence_id,),
    ).fetchone()


def _normalise_material_items(material_items: list[dict[str, int]] | None) -> list[dict[str, int]]:
    grouped: dict[int, int] = {}
    for item in material_items or []:
        stock_id = int(item.get("stock_id", 0) or 0)
        quantidade = int(item.get("quantidade", 0) or 0)
        if not stock_id or quantidade <= 0:
            continue
        grouped[stock_id] = grouped.get(stock_id, 0) + quantidade
    return [{"stock_id": stock_id, "quantidade": quantidade} for stock_id, quantidade in grouped.items()]


def create_budget(
    client_id: int,
    descricao: str,
    preco: float,
    include_iva: bool = True,
    valor_pago: float = 0.0,
    material_items: list[dict[str, int]] | None = None,
) -> tuple[int, float, float]:
    db = get_db()
    if not get_client(client_id):
        raise ValueError("Cliente não encontrado.")
    descricao = descricao.strip()
    if not descricao:
        raise ValueError("A descrição é obrigatória.")
    if preco < 0 or valor_pago < 0:
        raise ValueError("Os valores não podem ser negativos.")
    iva = round(preco * 0.23, 2) if include_iva else 0.0
    total = round(preco + iva, 2)
    normalised_items = _normalise_material_items(material_items)
    stock_rows: dict[int, sqlite3.Row] = {}

    for item in normalised_items:
        row = db.execute(
            "SELECT id, nome, quantidade FROM stock WHERE id = ?",
            (item["stock_id"],),
        ).fetchone()
        if row is None:
            raise ValueError("Um dos materiais escolhidos já não existe no stock.")
        if item["quantidade"] > int(row["quantidade"]):
            raise ValueError(
                f"Stock insuficiente para {row['nome']}. Disponível: {row['quantidade']}, pedido: {item['quantidade']}."
            )
        stock_rows[item["stock_id"]] = row

    try:
        cur = db.execute(
            """
            INSERT INTO orcamentos (cliente_id, data, descricao, preco, iva, total, include_iva, valor_pago)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                client_id,
                datetime.now().strftime("%d/%m/%Y"),
                descricao,
                preco,
                iva,
                total,
                1 if include_iva else 0,
                valor_pago,
            ),
        )
        budget_id = int(cur.lastrowid)
        now = datetime.now().strftime("%d/%m/%Y %H:%M")

        for item in normalised_items:
            row = stock_rows[item["stock_id"]]
            stock_before = int(row["quantidade"])
            stock_after = stock_before - item["quantidade"]
            db.execute(
                "UPDATE stock SET quantidade = ?, atualizado_em = ? WHERE id = ?",
                (stock_after, now, item["stock_id"]),
            )
            db.execute(
                """
                INSERT INTO orcamento_materiais
                    (orcamento_id, stock_id, nome_material, quantidade, stock_antes, stock_depois, data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (budget_id, item["stock_id"], row["nome"], item["quantidade"], stock_before, stock_after, now),
            )
        db.commit()
        return budget_id, iva, total
    except Exception:
        db.rollback()
        raise


def update_budget(
    budget_id: int,
    client_id: int,
    descricao: str,
    preco: float,
    include_iva: bool,
    valor_pago: float,
    material_items: list[dict[str, int]],
) -> tuple[int, float, float]:
    if client_id <= 0:
        raise ValueError("Selecione um cliente.")
    descricao = descricao.strip()
    if not descricao:
        raise ValueError("A descrição é obrigatória.")
    if preco < 0 or valor_pago < 0:
        raise ValueError("Os valores não podem ser negativos.")

    db = get_db()
    if not get_budget(budget_id):
        raise ValueError("Orçamento não encontrado.")

    iva = round(preco * 0.23, 2) if include_iva else 0.0
    total = round(preco + iva, 2)
    normalised_items = _normalise_material_items(material_items)

    _restore_budget_stock(db, budget_id)
    db.execute("DELETE FROM orcamento_materiais WHERE orcamento_id = ?", (budget_id,))

    stock_rows: dict[int, sqlite3.Row] = {}
    for item in normalised_items:
        row = db.execute(
            "SELECT id, nome, quantidade FROM stock WHERE id = ?",
            (item["stock_id"],),
        ).fetchone()
        if row is None:
            raise ValueError("Um dos materiais escolhidos já não existe no stock.")
        if item["quantidade"] > int(row["quantidade"]):
            raise ValueError(
                f"Stock insuficiente para {row['nome']}. Disponível: {row['quantidade']}, pedido: {item['quantidade']}."
            )
        stock_rows[item["stock_id"]] = row

    try:
        db.execute(
            """
            UPDATE orcamentos
            SET cliente_id = ?, descricao = ?, preco = ?, iva = ?, total = ?, include_iva = ?, valor_pago = ?, data = ?
            WHERE id = ?
            """,
            (
                client_id,
                descricao,
                preco,
                iva,
                total,
                1 if include_iva else 0,
                valor_pago,
                datetime.now().strftime("%d/%m/%Y"),
                budget_id,
            ),
        )

        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        for item in normalised_items:
            row = stock_rows[item["stock_id"]]
            stock_before = int(row["quantidade"])
            stock_after = stock_before - item["quantidade"]
            db.execute(
                "UPDATE stock SET quantidade = ?, atualizado_em = ? WHERE id = ?",
                (stock_after, now, item["stock_id"]),
            )
            db.execute(
                """
                INSERT INTO orcamento_materiais
                    (orcamento_id, stock_id, nome_material, quantidade, stock_antes, stock_depois, data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    budget_id,
                    item["stock_id"],
                    row["nome"],
                    item["quantidade"],
                    stock_before,
                    stock_after,
                    now,
                ),
            )
        db.commit()
        return budget_id, iva, total
    except Exception:
        db.rollback()
        raise


def list_budgets(client_id: int | None = None) -> list[sqlite3.Row]:
    params: tuple[Any, ...] = ()
    where = ""
    if client_id:
        where = "WHERE o.cliente_id = ?"
        params = (client_id,)
    return get_db().execute(
        f"""
        SELECT o.*, c.nome AS cliente_nome
        FROM orcamentos o
        LEFT JOIN clientes c ON c.id = o.cliente_id
        {where}
        ORDER BY o.id DESC
        """,
        params,
    ).fetchall()


def get_budget(budget_id: int) -> sqlite3.Row | None:
    return get_db().execute(
        """
        SELECT o.*, c.nome AS cliente_nome
        FROM orcamentos o
        LEFT JOIN clientes c ON c.id = o.cliente_id
        WHERE o.id = ?
        """,
        (budget_id,),
    ).fetchone()


def list_budget_materials(budget_id: int) -> list[sqlite3.Row]:
    return get_db().execute(
        """
        SELECT id, orcamento_id, stock_id, nome_material, quantidade, stock_antes, stock_depois, data
        FROM orcamento_materiais
        WHERE orcamento_id = ?
        ORDER BY id
        """,
        (budget_id,),
    ).fetchall()


def list_budget_materials_for_budgets(budget_ids: list[int]) -> dict[int, list[sqlite3.Row]]:
    if not budget_ids:
        return {}
    placeholders = ",".join("?" for _ in budget_ids)
    rows = get_db().execute(
        f"""
        SELECT id, orcamento_id, stock_id, nome_material, quantidade, stock_antes, stock_depois, data
        FROM orcamento_materiais
        WHERE orcamento_id IN ({placeholders})
        ORDER BY id
        """,
        tuple(budget_ids),
    ).fetchall()
    grouped: dict[int, list[sqlite3.Row]] = {budget_id: [] for budget_id in budget_ids}
    for row in rows:
        grouped.setdefault(int(row["orcamento_id"]), []).append(row)
    return grouped


def _restore_budget_stock(db: sqlite3.Connection, budget_id: int) -> None:
    rows = db.execute(
        "SELECT stock_id, quantidade FROM orcamento_materiais WHERE orcamento_id = ? AND stock_id IS NOT NULL",
        (budget_id,),
    ).fetchall()
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    for row in rows:
        db.execute(
            """
            UPDATE stock
            SET quantidade = quantidade + ?, atualizado_em = ?
            WHERE id = ?
            """,
            (int(row["quantidade"]), now, int(row["stock_id"])),
        )


def delete_budget(budget_id: int) -> int:
    db = get_db()
    _restore_budget_stock(db, budget_id)
    restored = db.execute(
        "SELECT COALESCE(SUM(quantidade), 0) FROM orcamento_materiais WHERE orcamento_id = ?",
        (budget_id,),
    ).fetchone()[0]
    db.execute("DELETE FROM orcamento_materiais WHERE orcamento_id = ?", (budget_id,))
    db.execute("DELETE FROM orcamentos WHERE id = ?", (budget_id,))
    db.commit()
    return int(restored or 0)


def add_stock(nome: str, categoria: str = "", quantidade: int = 0, stock_minimo: int = 0, localizacao: str = "", notas: str = "") -> int:
    nome = nome.strip()
    if not nome:
        raise ValueError("O material é obrigatório.")
    if quantidade < 0 or stock_minimo < 0:
        raise ValueError("As quantidades não podem ser negativas.")
    cur = get_db().execute(
        """
        INSERT INTO stock (nome, categoria, quantidade, stock_minimo, localizacao, notas, atualizado_em)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            nome,
            categoria.strip(),
            quantidade,
            stock_minimo,
            localizacao.strip(),
            notas.strip(),
            datetime.now().strftime("%d/%m/%Y %H:%M"),
        ),
    )
    get_db().commit()
    return int(cur.lastrowid)


def list_stock(term: str = "", low_only: bool = False) -> list[sqlite3.Row]:
    query = """
        SELECT id, nome, categoria, quantidade, stock_minimo, localizacao, notas, atualizado_em
        FROM stock
        WHERE (nome LIKE ? OR categoria LIKE ? OR localizacao LIKE ? OR notas LIKE ?)
    """
    params: list[Any] = [f"%{term}%", f"%{term}%", f"%{term}%", f"%{term}%"]
    if low_only:
        query += " AND stock_minimo > 0 AND quantidade <= stock_minimo"
    query += """
        ORDER BY
            CASE WHEN stock_minimo > 0 AND quantidade <= stock_minimo THEN 0 ELSE 1 END,
            nome COLLATE NOCASE
    """
    return get_db().execute(query, params).fetchall()


def update_stock_quantity(material_id: int, quantidade: int) -> None:
    if quantidade < 0:
        raise ValueError("A quantidade não pode ser negativa.")
    cur = get_db().execute(
        "UPDATE stock SET quantidade = ?, atualizado_em = ? WHERE id = ?",
        (quantidade, datetime.now().strftime("%d/%m/%Y %H:%M"), material_id),
    )
    get_db().commit()
    if cur.rowcount == 0:
        raise ValueError("Material não encontrado.")


def increment_stock_quantity(material_id: int, delta: int) -> int:
    db = get_db()
    row = db.execute("SELECT quantidade FROM stock WHERE id = ?", (material_id,)).fetchone()
    if row is None:
        raise ValueError("Material não encontrado.")
    quantidade = max(0, int(row["quantidade"]) + delta)
    db.execute(
        "UPDATE stock SET quantidade = ?, atualizado_em = ? WHERE id = ?",
        (quantidade, datetime.now().strftime("%d/%m/%Y %H:%M"), material_id),
    )
    db.commit()
    return quantidade


def delete_stock(material_id: int) -> None:
    get_db().execute("DELETE FROM stock WHERE id = ?", (material_id,))
    get_db().commit()


def count_low_stock() -> int:
    return int(
        get_db()
        .execute("SELECT COUNT(*) FROM stock WHERE stock_minimo > 0 AND quantidade <= stock_minimo")
        .fetchone()[0]
    )


def dashboard_data() -> dict[str, Any]:
    db = get_db()
    summary = db.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM clientes) AS clientes,
            (SELECT COUNT(*) FROM ocorrencias) AS ocorrencias,
            (SELECT COUNT(*) FROM orcamentos) AS orcamentos,
            (SELECT COUNT(*) FROM stock) AS materiais,
            (SELECT COUNT(*) FROM stock WHERE stock_minimo > 0 AND quantidade <= stock_minimo) AS stock_baixo,
            (SELECT COALESCE(SUM(total), 0) FROM orcamentos) AS total_orcamentado,
            (SELECT COALESCE(SUM(valor_pago), 0) FROM orcamentos) AS total_pago,
            (SELECT COALESCE(SUM(total - COALESCE(valor_pago, 0)), 0) FROM orcamentos) AS total_em_aberto
        """
    ).fetchone()
    recentes_ocorrencias = db.execute(
        """
        SELECT o.id, o.data, o.descricao, c.nome AS cliente_nome
        FROM ocorrencias o
        LEFT JOIN clientes c ON c.id = o.cliente_id
        ORDER BY o.id DESC
        LIMIT 5
        """
    ).fetchall()
    recentes_orcamentos = db.execute(
        """
        SELECT o.id, o.data, o.total, o.valor_pago, c.nome AS cliente_nome
        FROM orcamentos o
        LEFT JOIN clientes c ON c.id = o.cliente_id
        ORDER BY o.id DESC
        LIMIT 5
        """
    ).fetchall()
    return {
        "summary": summary,
        "stock_baixo": list_stock("", True)[:5],
        "recentes_ocorrencias": recentes_ocorrencias,
        "recentes_orcamentos": recentes_orcamentos,
    }


def create_backup() -> Path:
    db_path = Path(current_app.config["DATABASE"])
    backup_dir = Path(current_app.config["BACKUP_DIR"])
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"scootprime_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    get_db().commit()
    shutil.copy2(db_path, backup_path)
    return backup_path


def restore_backup(source: Path) -> None:
    if not source.exists():
        raise FileNotFoundError("Ficheiro de backup não encontrado.")
    close_db()
    db_path = Path(current_app.config["DATABASE"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, db_path)
    init_db()
