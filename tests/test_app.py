from pathlib import Path
from io import BytesIO
import shutil
import unittest
from uuid import uuid4

from pypdf import PdfReader

from scootprime_web import create_app
from scootprime_web import storage


class ScootPrimeWebTest(unittest.TestCase):
    def setUp(self):
        test_root = Path(__file__).resolve().parents[1] / "instance" / "_test_tmp"
        test_root.mkdir(parents=True, exist_ok=True)
        root = test_root / uuid4().hex
        root.mkdir()
        self.root = root
        self.app = create_app(
            {
                "TESTING": True,
                "DATABASE": str(root / "scootprime.db"),
                "BACKUP_DIR": str(root / "backups"),
                "BRAND_DIR": str(root / "brand"),
                "SECRET_KEY": "test",
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            storage.close_db()
        shutil.rmtree(self.root, ignore_errors=True)

    def login(self, password="segredo1"):
        with self.app.app_context():
            if not storage.has_users():
                storage.create_user("admin", "segredo1")
        return self.client.post(
            "/login",
            data={"username": "admin", "password": password},
            follow_redirects=True,
        )

    def test_first_user_setup(self):
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Criar primeiro acesso", response.data)

        response = self.client.post(
            "/login",
            data={"username": "manuel", "password": "segredo1", "confirm_password": "segredo1"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Visao rapida", response.data)

    def test_duplicate_user_creation_is_rejected(self):
        with self.app.app_context():
            storage.create_user("admin", "segredo1")
            with self.assertRaises(ValueError) as exc:
                storage.create_user("admin", "segredo2")
        self.assertIn("já existe", str(exc.exception))

    def test_password_can_be_changed_from_maintenance(self):
        self.login()
        response = self.client.post(
            "/manutencao",
            data={
                "action": "change_password",
                "current_password": "segredo1",
                "new_password": "nova123",
                "confirm_password": "nova123",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Password atualizada com sucesso.".encode(), response.data)

        self.client.get("/logout")
        response = self.login("segredo1")
        self.assertIn("Utilizador ou password inválido.".encode(), response.data)

        self.client.get("/logout")
        response = self.login("nova123")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Visao rapida", response.data)

    def test_password_change_rejects_wrong_current_password(self):
        self.login()
        response = self.client.post(
            "/manutencao",
            data={
                "action": "change_password",
                "current_password": "errada",
                "new_password": "nova123",
                "confirm_password": "nova123",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("A password atual está incorreta.".encode(), response.data)

        with self.app.app_context():
            self.assertIsNotNone(storage.verify_user("admin", "segredo1"))
            self.assertIsNone(storage.verify_user("admin", "nova123"))

    def test_main_pages_load(self):
        response = self.client.get("/painel")
        self.assertEqual(response.status_code, 302)

        self.login()
        for path in ["/painel", "/clientes", "/ocorrencias", "/orcamentos", "/pesquisa", "/stock", "/manutencao"]:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)

    def test_brand_logo_upload_and_serving(self):
        self.login()
        png = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
            b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
            b"\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?"
            b"\x00\x05\xfe\x02\xfeA\xde\xfc\xd8\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        response = self.client.post(
            "/manutencao",
            data={
                "action": "brand_logo",
                "brand_logo": (BytesIO(png), "marca.png"),
            },
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Imagem da marca atualizada com sucesso.".encode(), response.data)

        response = self.client.get("/marca/imagem")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, png)
        response.close()

    def test_client_and_stock_flow(self):
        self.login()
        response = self.client.post(
            "/clientes",
            data={"nome": "Cliente Teste", "morada": "Rua A", "contacto": "900000000"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Cliente Teste", response.data)

        response = self.client.post(
            "/stock",
            data={
                "action": "add",
                "nome": "Pneu 10",
                "categoria": "Rodas",
                "quantidade": "2",
                "stock_minimo": "1",
                "localizacao": "A1",
                "notas": "",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Pneu 10", response.data)

        response = self.client.post(
            "/stock",
            data={"action": "delta", "material_id": "1", "delta": "1"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b">3<", response.data)

    def test_budget_consumes_stock_atomically(self):
        self.login()
        with self.app.app_context():
            client_id = storage.add_client("Cliente Stock", "Rua B", "911111111")
            material_id = storage.add_stock("Pastilhas travao", "Travagem", 5, 1, "B2", "")

        response = self.client.post(
            "/orcamentos",
            data={
                "cliente_id": str(client_id),
                "descricao": "Troca de pastilhas",
                "preco": "25",
                "include_iva": "on",
                "valor_pago": "0",
                "material_id": str(material_id),
                "material_qty": "2",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Pastilhas travao x2", response.data)

        with self.app.app_context():
            stock = storage.list_stock("Pastilhas")[0]
            self.assertEqual(stock["quantidade"], 3)
            budgets = storage.list_budgets(client_id)
            materials = storage.list_budget_materials(budgets[0]["id"])
            self.assertEqual(materials[0]["stock_antes"], 5)
            self.assertEqual(materials[0]["stock_depois"], 3)

    def test_budget_pdf_has_professional_layout_content(self):
        self.login()
        with self.app.app_context():
            storage.save_store_profile("Loja Teste", "Reparacao Premium", "910000000", "Rua da Loja")
            client_id = storage.add_client("Cliente PDF", "Rua do Teste", "955555555")
            material_id = storage.add_stock("Pneu premium", "Rodas", 4, 1, "A1", "")
            budget_id = storage.create_budget(
                client_id,
                "Substituicao de pneu e verificacao geral",
                50.0,
                True,
                10.0,
                [{"stock_id": material_id, "quantidade": 1}],
            )[0]

        response = self.client.get(f"/orcamentos/{budget_id}/pdf")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/pdf")
        self.assertIn(f"ORC_{budget_id}_", response.headers["Content-Disposition"])

        reader = PdfReader(BytesIO(response.data))
        text = reader.pages[0].extract_text()
        self.assertIn("ORCAMENTO", text)
        self.assertIn(f"ORC-{budget_id}-", text)
        self.assertIn("Loja Teste", text)
        self.assertIn("Rua da Loja", text)
        self.assertIn("Cliente PDF", text)
        self.assertIn("Servico de reparacao", text)
        self.assertIn("Pneu premium", text)
        self.assertIn("TOTAL", text.upper())
        response.close()

    def test_occurrence_pdf_uses_store_profile(self):
        self.login()
        with self.app.app_context():
            storage.save_store_profile("Oficina Central", "Assistencia Tecnica", "912345678", "Avenida Principal 10")
            client_id = storage.add_client("Cliente Ocorrencia", "Rua Cliente", "966666666")
            occurrence_id = storage.add_occurrence(client_id, "Barulho no motor traseiro e folga no guiador.")

        response = self.client.get(f"/ocorrencias/{occurrence_id}/pdf")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/pdf")
        self.assertIn(f"OCC_{occurrence_id}_", response.headers["Content-Disposition"])

        reader = PdfReader(BytesIO(response.data))
        text = reader.pages[0].extract_text()
        self.assertIn("OCORRENCIA", text)
        self.assertIn(f"OCC-{occurrence_id}-", text)
        self.assertIn("Oficina Central", text)
        self.assertIn("Avenida Principal 10", text)
        self.assertIn("Cliente Ocorrencia", text)
        self.assertIn("Barulho no motor traseiro", text)
        self.assertNotIn("Seguimento interno", text)
        self.assertNotIn("Diagnostico", text)
        response.close()

    def test_stock_reports_pdf_existing_and_restock(self):
        self.login()
        with self.app.app_context():
            storage.add_stock("Pneu premium", "Rodas", 6, 2, "A1", "")
            storage.add_stock("Pastilhas", "Travagem", 1, 3, "B1", "")

        response = self.client.get("/stock/pdf")
        self.assertEqual(response.status_code, 200)
        self.assertIn("STOCK_EXISTENTE_", response.headers["Content-Disposition"])
        text = PdfReader(BytesIO(response.data)).pages[0].extract_text()
        self.assertIn("Stock existente", text)
        self.assertIn("Pneu premium", text)
        self.assertIn("Pastilhas", text)
        response.close()

        response = self.client.get("/stock/pdf?tipo=reposicao")
        self.assertEqual(response.status_code, 200)
        self.assertIn("STOCK_REPOSICAO_", response.headers["Content-Disposition"])
        text = PdfReader(BytesIO(response.data)).pages[0].extract_text()
        self.assertIn("Material em falta", text)
        self.assertIn("Pastilhas", text)
        self.assertNotIn("Pneu premium", text)
        response.close()

    def test_backup_can_be_downloaded_and_deleted(self):
        self.login()
        response = self.client.post("/manutencao", data={"action": "backup"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Descarregar".encode(), response.data)

        backups = sorted(Path(self.app.config["BACKUP_DIR"]).glob("*.db"))
        self.assertEqual(len(backups), 1)
        backup_name = backups[0].name

        response = self.client.get(f"/manutencao/backups/{backup_name}/descarregar")
        self.assertEqual(response.status_code, 200)
        self.assertIn(backup_name, response.headers["Content-Disposition"])
        self.assertGreater(len(response.data), 0)
        response.close()

        response = self.client.post(
            f"/manutencao/backups/{backup_name}/eliminar",
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(backups[0].exists())

    def test_store_profile_can_be_updated_from_maintenance(self):
        self.login()
        response = self.client.post(
            "/manutencao",
            data={
                "action": "store_profile",
                "store_name": "Minha Loja",
                "store_subtitle": "Reparacoes Urbanas",
                "store_contact": "919999999",
                "store_address": "Rua Nova 22",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Dados da loja atualizados com sucesso.".encode(), response.data)

        with self.app.app_context():
            profile = storage.get_store_profile()
            self.assertEqual(profile["store_name"], "Minha Loja")
            self.assertEqual(profile["store_contact"], "919999999")

    def test_edit_budget_restores_and_consumes_stock(self):
        self.login()
        with self.app.app_context():
            client_id = storage.add_client("Cliente Edit", "Rua C", "922222222")
            original_material_id = storage.add_stock("Cabo acelerador", "Cabos", 5, 1, "C3", "")
            new_material_id = storage.add_stock("Cabo embraiagem", "Cabos", 4, 1, "C3", "")
            budget_id = storage.create_budget(
                client_id,
                "Ajuste de cabo",
                30.0,
                True,
                0.0,
                [{"stock_id": original_material_id, "quantidade": 1}],
            )[0]

        response = self.client.post(
            f"/orcamentos/{budget_id}/editar",
            data={
                "cliente_id": str(client_id),
                "descricao": "Ajuste de cabo atualizado",
                "preco": "40",
                "include_iva": "on",
                "valor_pago": "10",
                "material_id": str(new_material_id),
                "material_qty": "2",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Orçamento atualizado com sucesso.".encode(), response.data)

        with self.app.app_context():
            budget = storage.get_budget(budget_id)
            self.assertEqual(budget["descricao"], "Ajuste de cabo atualizado")
            self.assertEqual(float(budget["valor_pago"] or 0), 10.0)
            self.assertEqual(storage.list_stock("Cabo acelerador")[0]["quantidade"], 5)
            self.assertEqual(storage.list_stock("Cabo embraiagem")[0]["quantidade"], 2)

    def test_edit_client_updates_details_and_search(self):
        self.login()
        with self.app.app_context():
            client_id = storage.add_client("Cliente Editar", "Rua D", "933333333")

        response = self.client.post(
            f"/clientes/{client_id}/editar",
            data={
                "nome": "Cliente Editado",
                "morada": "Nova Rua",
                "contacto": "944444444",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Cliente atualizado com sucesso.".encode(), response.data)

        with self.app.app_context():
            client = storage.get_client(client_id)
            self.assertEqual(client["nome"], "Cliente Editado")
            self.assertEqual(client["morada"], "Nova Rua")
            self.assertEqual(client["contacto"], "944444444")

        # search page should link to the edit page for the client
        response = self.client.get(f"/pesquisa?q=Cliente+Editado")
        self.assertEqual(response.status_code, 200)
        self.assertIn(f"/clientes/{client_id}/editar", response.get_data(as_text=True))

    def test_budget_does_not_save_when_stock_is_missing(self):
        self.login()
        with self.app.app_context():
            client_id = storage.add_client("Cliente Sem Stock", "", "")
            material_id = storage.add_stock("Camara ar", "Rodas", 1, 1, "C1", "")

        response = self.client.post(
            "/orcamentos",
            data={
                "cliente_id": str(client_id),
                "descricao": "Troca de camara",
                "preco": "12",
                "include_iva": "on",
                "valor_pago": "0",
                "material_id": str(material_id),
                "material_qty": "3",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Stock insuficiente", response.data)

        with self.app.app_context():
            self.assertEqual(storage.list_stock("Camara")[0]["quantidade"], 1)
            self.assertEqual(storage.list_budgets(client_id), [])


if __name__ == "__main__":
    unittest.main()
