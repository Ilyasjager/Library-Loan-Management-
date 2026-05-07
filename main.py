from __future__ import annotations

import csv
import hashlib
import hmac
import os
import sqlite3
from datetime import date, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "bibliotheque.db"
RESULT_DIR = APP_DIR / "resultat"
ICON_PNG_PATH = APP_DIR / "assets" / "library_icon.png"
ICON_ICO_PATH = APP_DIR / "assets" / "library_icon.ico"
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"
PASSWORD_ITERATIONS = 120_000
FINE_PER_DAY = 2
RETURN_SOON_DAYS = 2

COLORS = {
    "window": "#F2F2F2",
    "section": "#FFFFFF",
    "section_alt": "#F2F2F2",
    "input": "#FFFFFF",
    "title": "#333333",
    "text": "#555555",
    "muted": "#555555",
    "border": "#DDDDDD",
    "primary": "#2E86C1",
    "primary_hover": "#2874A6",
    "secondary": "#DDDDDD",
    "secondary_hover": "#D6EAF8",
    "danger": "#C0392B",
    "danger_hover": "#A93226",
    "selected": "#D6EAF8",
    "white": "#FFFFFF",
    "black": "#333333",
}

TEXTS = {
    "fr": {
        "app_title": "Application de gestion des emprunts",
        "main_title": "Gestion des emprunts d'une bibliotheque",
        "books_tab": "Livres",
        "members_tab": "Membres",
        "loans_tab": "Emprunts",
        "stats_tab": "Statistiques",
        "language": "Langue",
        "book_form": "Formulaire livre",
        "member_form": "Formulaire membre",
        "new_loan": "Nouvel emprunt",
        "title": "Titre",
        "author": "Auteur",
        "genre": "Genre",
        "year": "Annee",
        "copies": "Exemplaires",
        "total": "Total",
        "available": "Disponibles",
        "name": "Nom",
        "first_name": "Prenom",
        "email": "Email",
        "member_number": "Numero adhesion",
        "book": "Livre",
        "member": "Membre",
        "loan_date": "Date emprunt",
        "due_date": "Retour prevu",
        "status": "Statut",
        "penalty": "Penalite",
        "add": "Ajouter",
        "edit": "Modifier",
        "delete": "Supprimer",
        "clear": "Vider",
        "search": "Rechercher",
        "refresh": "Actualiser",
        "borrow": "Emprunter",
        "return_book": "Retour livre",
        "book_search": "Recherche titre/auteur",
        "member_search": "Recherche nom/numero",
        "loan_search": "Recherche membre/livre",
        "stock_books": "Livres en stock",
        "available_copies": "Exemplaires disponibles",
        "active_loans": "Emprunts en cours",
        "overdue_loans": "Retards",
        "most_borrowed": "Livres les plus empruntes",
        "loan_count": "Nombre d'emprunts",
        "export_report_pdf": "Exporter rapport PDF",
        "export_late_pdf": "Exporter retards PDF",
        "export_report": "Exporter rapport CSV",
        "export_late": "Exporter retards CSV",
        "credit": "Cette application a ete creee par Ilyas El Bahi",
        "status_ok": "A jour",
        "status_due_soon": "Retour imminent",
        "status_late": "En retard",
    },
    "en": {
        "app_title": "Loan management application",
        "main_title": "Library loan management",
        "books_tab": "Books",
        "members_tab": "Members",
        "loans_tab": "Loans",
        "stats_tab": "Statistics",
        "language": "Language",
        "book_form": "Book form",
        "member_form": "Member form",
        "new_loan": "New loan",
        "title": "Title",
        "author": "Author",
        "genre": "Genre",
        "year": "Year",
        "copies": "Copies",
        "total": "Total",
        "available": "Available",
        "name": "Last name",
        "first_name": "First name",
        "email": "Email",
        "member_number": "Membership no.",
        "book": "Book",
        "member": "Member",
        "loan_date": "Loan date",
        "due_date": "Due date",
        "status": "Status",
        "penalty": "Fine",
        "add": "Add",
        "edit": "Edit",
        "delete": "Delete",
        "clear": "Clear",
        "search": "Search",
        "refresh": "Refresh",
        "borrow": "Borrow",
        "return_book": "Return",
        "book_search": "Search title/author",
        "member_search": "Search name/number",
        "loan_search": "Search member/book",
        "stock_books": "Books in stock",
        "available_copies": "Available copies",
        "active_loans": "Active loans",
        "overdue_loans": "Late loans",
        "most_borrowed": "Most borrowed books",
        "loan_count": "Loans count",
        "export_report_pdf": "Export PDF report",
        "export_late_pdf": "Export late PDF",
        "export_report": "Export CSV report",
        "export_late": "Export late CSV",
        "credit": "This application was created by Ilyas El Bahi",
        "status_ok": "On time",
        "status_due_soon": "Due soon",
        "status_late": "Late",
    },
}


def parse_iso_date(value: str) -> date:
    return date.fromisoformat(value)


class PdfReport:
    def __init__(self, path: str, title: str, subtitle: str = "") -> None:
        self.path = path
        self.title = title
        self.subtitle = subtitle
        self.width = 595
        self.height = 842
        self.margin = 38
        self.pages: list[list[str]] = []
        self.commands: list[str] = []
        self.y = 0
        self.new_page()

    def new_page(self) -> None:
        if self.commands:
            self.pages.append(self.commands)
        self.commands = []
        self.draw_rect(0, self.height - 74, self.width, 74, "#2E86C1")
        self.draw_text(self.margin, self.height - 34, self.title, 18, True, "#FFFFFF")
        if self.subtitle:
            self.draw_text(self.margin, self.height - 55, self.subtitle, 9, False, "#FFFFFF")
        self.y = self.height - 100

    def save(self) -> None:
        if self.commands:
            self.pages.append(self.commands)
            self.commands = []

        objects: dict[int, bytes] = {}
        page_ids = []
        next_id = 5
        for commands in self.pages:
            page_id = next_id
            content_id = next_id + 1
            next_id += 2
            page_ids.append(page_id)
            stream = "\n".join(commands).encode("latin-1", "replace")
            objects[content_id] = (
                f"<< /Length {len(stream)} >>\nstream\n".encode("ascii")
                + stream
                + b"\nendstream"
            )
            objects[page_id] = (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self.width} {self.height}] "
                f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
                f"/Contents {content_id} 0 R >>"
            ).encode("ascii")

        kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
        objects[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
        objects[2] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("ascii")
        objects[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
        objects[4] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"

        ordered_ids = sorted(objects)
        pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = {0: 0}
        for obj_id in ordered_ids:
            offsets[obj_id] = len(pdf)
            pdf.extend(f"{obj_id} 0 obj\n".encode("ascii"))
            pdf.extend(objects[obj_id])
            pdf.extend(b"\nendobj\n")

        xref_start = len(pdf)
        pdf.extend(f"xref\n0 {max(ordered_ids) + 1}\n".encode("ascii"))
        pdf.extend(b"0000000000 65535 f \n")
        for obj_id in range(1, max(ordered_ids) + 1):
            pdf.extend(f"{offsets.get(obj_id, 0):010d} 00000 n \n".encode("ascii"))
        pdf.extend(
            (
                f"trailer\n<< /Size {max(ordered_ids) + 1} /Root 1 0 R >>\n"
                f"startxref\n{xref_start}\n%%EOF"
            ).encode("ascii")
        )

        Path(self.path).write_bytes(bytes(pdf))

    def ensure_space(self, height_needed: int) -> None:
        if self.y - height_needed < self.margin:
            self.new_page()

    def draw_text(
        self,
        x: float,
        y: float,
        text: str,
        size: int = 10,
        bold: bool = False,
        color: str = "#333333",
    ) -> None:
        font = "F2" if bold else "F1"
        r, g, b = self.rgb(color)
        self.commands.append(
            f"BT /{font} {size} Tf {r:.3f} {g:.3f} {b:.3f} rg "
            f"{x:.2f} {y:.2f} Td ({self.pdf_text(text)}) Tj ET"
        )

    def draw_rect(self, x: float, y: float, width: float, height: float, color: str) -> None:
        r, g, b = self.rgb(color)
        self.commands.append(
            f"q {r:.3f} {g:.3f} {b:.3f} rg {x:.2f} {y:.2f} "
            f"{width:.2f} {height:.2f} re f Q"
        )

    def add_section(self, title: str) -> None:
        self.ensure_space(40)
        self.draw_rect(self.margin, self.y - 24, self.width - self.margin * 2, 24, "#2E86C1")
        self.draw_text(self.margin + 10, self.y - 17, title, 11, True, "#FFFFFF")
        self.y -= 34

    def add_kpis(self, items: list[tuple[str, str | int]], danger_index: int | None = None) -> None:
        card_width = (self.width - self.margin * 2 - 20) / 3
        card_height = 52
        for index, (label, value) in enumerate(items):
            row = index // 3
            col = index % 3
            x = self.margin + col * (card_width + 10)
            y_top = self.y - row * (card_height + 10)
            fill = "#FEE2E2" if danger_index == index else "#DBEAFE"
            text_color = "#991B1B" if danger_index == index else "#1E3A8A"
            self.draw_rect(x, y_top - card_height, card_width, card_height, fill)
            self.draw_text(x + 10, y_top - 20, str(label), 9, True, text_color)
            self.draw_text(x + 10, y_top - 40, str(value), 15, True, text_color)
        rows = (len(items) + 2) // 3
        self.y -= rows * (card_height + 10) + 12

    def add_table(
        self,
        title: str,
        headers: list[str],
        rows: list[list[str | int]],
        widths: list[int],
    ) -> None:
        self.add_section(title)
        self.draw_table_header(headers, widths)
        for index, row in enumerate(rows):
            self.ensure_space(20)
            fill = "#FFFFFF" if index % 2 == 0 else "#F8FAFC"
            self.draw_rect(self.margin, self.y - 18, sum(widths), 18, fill)
            x = self.margin
            for header, value, width in zip(headers, row, widths):
                color = self.status_color(header, str(value))
                self.draw_text(x + 4, self.y - 13, self.fit_text(str(value), width), 8, False, color)
                x += width
            self.y -= 18
        self.y -= 18

    def draw_table_header(self, headers: list[str], widths: list[int]) -> None:
        self.ensure_space(24)
        self.draw_rect(self.margin, self.y - 20, sum(widths), 20, "#333333")
        x = self.margin
        for header, width in zip(headers, widths):
            self.draw_text(x + 4, self.y - 14, self.fit_text(header, width), 8, True, "#FFFFFF")
            x += width
        self.y -= 20

    @staticmethod
    def rgb(color: str) -> tuple[float, float, float]:
        color = color.lstrip("#")
        return (
            int(color[0:2], 16) / 255,
            int(color[2:4], 16) / 255,
            int(color[4:6], 16) / 255,
        )

    @staticmethod
    def pdf_text(text: str) -> str:
        encoded = text.encode("cp1252", "replace").decode("latin-1")
        return encoded.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    @staticmethod
    def fit_text(text: str, width: int) -> str:
        max_chars = max(6, int(width / 4.4))
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 1] + "…"

    @staticmethod
    def status_color(header: str, value: str) -> str:
        if header.lower().startswith("statut") or header.lower().startswith("status"):
            value = value.lower()
            if "retard" in value or "late" in value:
                return "#B91C1C"
            if "rendu" in value or "returned" in value:
                return "#1D4ED8"
            return "#166534"
        return "#333333"


class DatabaseManager:
    """Couche simple pour isoler toutes les operations SQLite."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.initialize_database()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize_database(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS livres (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titre TEXT NOT NULL,
                    auteur TEXT NOT NULL,
                    genre TEXT,
                    annee INTEGER,
                    total_exemplaires INTEGER NOT NULL CHECK(total_exemplaires >= 0),
                    exemplaires_disponibles INTEGER NOT NULL CHECK(exemplaires_disponibles >= 0)
                );

                CREATE TABLE IF NOT EXISTS membres (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    prenom TEXT NOT NULL,
                    email TEXT,
                    numero_adhesion TEXT NOT NULL UNIQUE
                );

                CREATE TABLE IF NOT EXISTS emprunts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    livre_id INTEGER NOT NULL,
                    membre_id INTEGER NOT NULL,
                    date_emprunt TEXT NOT NULL,
                    date_retour_prevue TEXT NOT NULL,
                    date_retour_reelle TEXT,
                    FOREIGN KEY(livre_id) REFERENCES livres(id),
                    FOREIGN KEY(membre_id) REFERENCES membres(id)
                );

                CREATE TABLE IF NOT EXISTS administrateurs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            self.ensure_default_admin(connection)

    def ensure_default_admin(self, connection: sqlite3.Connection) -> None:
        row = connection.execute(
            "SELECT COUNT(*) AS count FROM administrateurs"
        ).fetchone()
        if int(row["count"]) > 0:
            return

        salt = os.urandom(16).hex()
        password_hash = self.hash_password(DEFAULT_ADMIN_PASSWORD, salt)
        connection.execute(
            """
            INSERT INTO administrateurs
                (username, password_hash, salt, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                DEFAULT_ADMIN_USERNAME,
                password_hash,
                salt,
                date.today().isoformat(),
            ),
        )

    @staticmethod
    def hash_password(password: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            PASSWORD_ITERATIONS,
        ).hex()

    def verify_admin_login(self, username: str, password: str) -> bool:
        with self.connect() as connection:
            admin = connection.execute(
                """
                SELECT password_hash, salt
                FROM administrateurs
                WHERE username = ?
                """,
                (username,),
            ).fetchone()

        if admin is None:
            return False

        password_hash = self.hash_password(password, admin["salt"])
        return hmac.compare_digest(password_hash, admin["password_hash"])

    def list_books(self, search: str = "") -> list[sqlite3.Row]:
        query = """
            SELECT id, titre, auteur, genre, annee, total_exemplaires,
                   exemplaires_disponibles
            FROM livres
        """
        params: tuple[str, ...] = ()
        search = search.strip().lower()
        if search:
            query += " WHERE lower(titre) LIKE ? OR lower(auteur) LIKE ?"
            params = (f"%{search}%", f"%{search}%")
        query += " ORDER BY titre, auteur"

        with self.connect() as connection:
            return connection.execute(query, params).fetchall()

    def get_book(self, book_id: int) -> sqlite3.Row | None:
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM livres WHERE id = ?",
                (book_id,),
            ).fetchone()

    def add_book(
        self,
        titre: str,
        auteur: str,
        genre: str,
        annee: int | None,
        total_exemplaires: int,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO livres
                    (titre, auteur, genre, annee, total_exemplaires,
                     exemplaires_disponibles)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    titre,
                    auteur,
                    genre,
                    annee,
                    total_exemplaires,
                    total_exemplaires,
                ),
            )

    def update_book(
        self,
        book_id: int,
        titre: str,
        auteur: str,
        genre: str,
        annee: int | None,
        total_exemplaires: int,
    ) -> None:
        active_loans = self.count_active_loans_for_book(book_id)
        if total_exemplaires < active_loans:
            raise ValueError(
                "Le total d'exemplaires ne peut pas etre inferieur aux "
                "emprunts en cours."
            )

        available = total_exemplaires - active_loans
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE livres
                SET titre = ?, auteur = ?, genre = ?, annee = ?,
                    total_exemplaires = ?, exemplaires_disponibles = ?
                WHERE id = ?
                """,
                (
                    titre,
                    auteur,
                    genre,
                    annee,
                    total_exemplaires,
                    available,
                    book_id,
                ),
            )

    def delete_book(self, book_id: int) -> None:
        if self.count_active_loans_for_book(book_id) > 0:
            raise ValueError("Ce livre a un emprunt actif et ne peut pas etre supprime.")

        with self.connect() as connection:
            connection.execute("DELETE FROM livres WHERE id = ?", (book_id,))

    def count_active_loans_for_book(self, book_id: int) -> int:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM emprunts
                WHERE livre_id = ? AND date_retour_reelle IS NULL
                """,
                (book_id,),
            ).fetchone()
        return int(row["count"])

    def list_members(self, search: str = "") -> list[sqlite3.Row]:
        query = "SELECT id, nom, prenom, email, numero_adhesion FROM membres"
        params: tuple[str, ...] = ()
        search = search.strip().lower()
        if search:
            query += """
                WHERE lower(nom) LIKE ?
                   OR lower(prenom) LIKE ?
                   OR lower(numero_adhesion) LIKE ?
            """
            params = (f"%{search}%", f"%{search}%", f"%{search}%")
        query += " ORDER BY nom, prenom"

        with self.connect() as connection:
            return connection.execute(query, params).fetchall()

    def get_member(self, member_id: int) -> sqlite3.Row | None:
        with self.connect() as connection:
            return connection.execute(
                "SELECT * FROM membres WHERE id = ?",
                (member_id,),
            ).fetchone()

    def add_member(
        self,
        nom: str,
        prenom: str,
        email: str,
        numero_adhesion: str,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO membres (nom, prenom, email, numero_adhesion)
                VALUES (?, ?, ?, ?)
                """,
                (nom, prenom, email, numero_adhesion),
            )

    def update_member(
        self,
        member_id: int,
        nom: str,
        prenom: str,
        email: str,
        numero_adhesion: str,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE membres
                SET nom = ?, prenom = ?, email = ?, numero_adhesion = ?
                WHERE id = ?
                """,
                (nom, prenom, email, numero_adhesion, member_id),
            )

    def delete_member(self, member_id: int) -> None:
        if self.count_active_loans_for_member(member_id) > 0:
            raise ValueError("Ce membre a un emprunt actif et ne peut pas etre supprime.")

        with self.connect() as connection:
            connection.execute("DELETE FROM membres WHERE id = ?", (member_id,))

    def count_active_loans_for_member(self, member_id: int) -> int:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM emprunts
                WHERE membre_id = ? AND date_retour_reelle IS NULL
                """,
                (member_id,),
            ).fetchone()
        return int(row["count"])

    def list_active_loans(self, search: str = "") -> list[sqlite3.Row]:
        query = """
            SELECT
                e.id,
                l.titre AS livre_titre,
                l.auteur AS livre_auteur,
                m.nom AS membre_nom,
                m.prenom AS membre_prenom,
                m.numero_adhesion,
                e.date_emprunt,
                e.date_retour_prevue
            FROM emprunts e
            JOIN livres l ON l.id = e.livre_id
            JOIN membres m ON m.id = e.membre_id
            WHERE e.date_retour_reelle IS NULL
        """
        params: tuple[str, ...] = ()
        search = search.strip().lower()
        if search:
            query += """
                AND (
                    lower(l.titre) LIKE ?
                    OR lower(l.auteur) LIKE ?
                    OR lower(m.nom) LIKE ?
                    OR lower(m.prenom) LIKE ?
                    OR lower(m.numero_adhesion) LIKE ?
                )
            """
            params = (
                f"%{search}%",
                f"%{search}%",
                f"%{search}%",
                f"%{search}%",
                f"%{search}%",
            )
        query += " ORDER BY e.date_retour_prevue, m.nom, l.titre"

        with self.connect() as connection:
            return connection.execute(query, params).fetchall()

    def list_all_loans(self) -> list[sqlite3.Row]:
        with self.connect() as connection:
            return connection.execute(
                """
                SELECT
                    e.id,
                    l.titre AS livre_titre,
                    l.auteur AS livre_auteur,
                    m.nom AS membre_nom,
                    m.prenom AS membre_prenom,
                    m.numero_adhesion,
                    e.date_emprunt,
                    e.date_retour_prevue,
                    e.date_retour_reelle
                FROM emprunts e
                JOIN livres l ON l.id = e.livre_id
                JOIN membres m ON m.id = e.membre_id
                ORDER BY e.date_emprunt DESC, m.nom, l.titre
                """
            ).fetchall()

    def get_loan_alert_counts(self) -> dict[str, int]:
        today = date.today()
        due_soon_limit = today + timedelta(days=RETURN_SOON_DAYS)
        overdue = 0
        due_soon = 0

        for loan in self.list_active_loans():
            due_date = parse_iso_date(loan["date_retour_prevue"])
            if due_date < today:
                overdue += 1
            elif due_date <= due_soon_limit:
                due_soon += 1

        return {"overdue": overdue, "due_soon": due_soon}

    def list_overdue_loans(self) -> list[sqlite3.Row]:
        today = date.today()
        return [
            loan
            for loan in self.list_active_loans()
            if parse_iso_date(loan["date_retour_prevue"]) < today
        ]

    def add_loan(self, book_id: int, member_id: int) -> None:
        today = date.today()
        due_date = today + timedelta(days=14)

        with self.connect() as connection:
            book = connection.execute(
                """
                SELECT id, titre, exemplaires_disponibles
                FROM livres
                WHERE id = ?
                """,
                (book_id,),
            ).fetchone()
            if book is None:
                raise ValueError("Livre introuvable.")

            if int(book["exemplaires_disponibles"]) <= 0:
                raise ValueError("Aucun exemplaire disponible pour ce livre.")

            member = connection.execute(
                "SELECT id FROM membres WHERE id = ?",
                (member_id,),
            ).fetchone()
            if member is None:
                raise ValueError("Membre introuvable.")

            existing = connection.execute(
                """
                SELECT id
                FROM emprunts
                WHERE livre_id = ?
                  AND membre_id = ?
                  AND date_retour_reelle IS NULL
                """,
                (book_id, member_id),
            ).fetchone()
            if existing is not None:
                raise ValueError(
                    "Ce membre a deja emprunte ce livre et ne l'a pas encore rendu."
                )

            connection.execute(
                """
                INSERT INTO emprunts
                    (livre_id, membre_id, date_emprunt, date_retour_prevue)
                VALUES (?, ?, ?, ?)
                """,
                (book_id, member_id, today.isoformat(), due_date.isoformat()),
            )
            connection.execute(
                """
                UPDATE livres
                SET exemplaires_disponibles = exemplaires_disponibles - 1
                WHERE id = ?
                """,
                (book_id,),
            )

    def return_loan(self, loan_id: int) -> None:
        today = date.today().isoformat()

        with self.connect() as connection:
            loan = connection.execute(
                """
                SELECT id, livre_id, date_retour_reelle
                FROM emprunts
                WHERE id = ?
                """,
                (loan_id,),
            ).fetchone()
            if loan is None:
                raise ValueError("Emprunt introuvable.")

            if loan["date_retour_reelle"] is not None:
                raise ValueError("Ce livre est deja rendu.")

            book = connection.execute(
                """
                SELECT total_exemplaires, exemplaires_disponibles
                FROM livres
                WHERE id = ?
                """,
                (loan["livre_id"],),
            ).fetchone()
            if book is None:
                raise ValueError("Livre lie a cet emprunt introuvable.")

            new_available = min(
                int(book["total_exemplaires"]),
                int(book["exemplaires_disponibles"]) + 1,
            )

            connection.execute(
                """
                UPDATE emprunts
                SET date_retour_reelle = ?
                WHERE id = ?
                """,
                (today, loan_id),
            )
            connection.execute(
                """
                UPDATE livres
                SET exemplaires_disponibles = ?
                WHERE id = ?
                """,
                (new_available, loan["livre_id"]),
            )

    def get_statistics(self) -> dict[str, int]:
        with self.connect() as connection:
            total_books = connection.execute(
                "SELECT COALESCE(SUM(total_exemplaires), 0) AS count FROM livres"
            ).fetchone()["count"]
            available = connection.execute(
                "SELECT COALESCE(SUM(exemplaires_disponibles), 0) AS count FROM livres"
            ).fetchone()["count"]
            members = connection.execute(
                "SELECT COUNT(*) AS count FROM membres"
            ).fetchone()["count"]
            active_loans = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM emprunts
                WHERE date_retour_reelle IS NULL
                """
            ).fetchone()["count"]

        overdue_loans = self.get_loan_alert_counts()["overdue"]

        return {
            "total_books": int(total_books),
            "available": int(available),
            "members": int(members),
            "active_loans": int(active_loans),
            "overdue_loans": int(overdue_loans),
        }

    def list_most_borrowed_books(self) -> list[sqlite3.Row]:
        with self.connect() as connection:
            return connection.execute(
                """
                SELECT l.titre, l.auteur, COUNT(e.id) AS emprunts
                FROM livres l
                JOIN emprunts e ON e.livre_id = l.id
                GROUP BY l.id, l.titre, l.auteur
                ORDER BY emprunts DESC, l.titre
                LIMIT 10
                """
            ).fetchall()


class LoginWindow:
    def __init__(self, root: tk.Tk, db: DatabaseManager, on_success) -> None:
        self.root = root
        self.db = db
        self.on_success = on_success
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.error_var = tk.StringVar()

        self.root.title("Connexion administrateur")
        self.root.tk.call("tk", "scaling", 1.25)
        self.root.geometry("720x520")
        self.root.minsize(720, 520)
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS["window"])

        self.set_window_icon()
        self.center_window(720, 520)
        self.create_widgets()
        self.root.bind("<Return>", lambda _event: self.login())

    def set_window_icon(self) -> None:
        try:
            if ICON_ICO_PATH.exists():
                self.root.iconbitmap(default=str(ICON_ICO_PATH))
            if ICON_PNG_PATH.exists():
                self.icon_image = tk.PhotoImage(file=str(ICON_PNG_PATH))
                self.root.iconphoto(True, self.icon_image)
        except tk.TclError:
            pass

    def center_window(self, width: int, height: int) -> None:
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self) -> None:
        page = tk.Frame(self.root, bg=COLORS["window"])
        page.pack(fill="both", expand=True)

        card = tk.Frame(
            page,
            bg=COLORS["section"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        card.place(relx=0.5, rely=0.48, anchor="center", width=520, height=392)

        tk.Label(
            card,
            text="Connexion admin",
            bg=COLORS["section"],
            fg=COLORS["title"],
            font=("Segoe UI", 25, "bold"),
        ).pack(anchor="w", padx=36, pady=(34, 4))
        tk.Label(
            card,
            text="Acces securise a la gestion de bibliotheque",
            bg=COLORS["section"],
            fg=COLORS["muted"],
            font=("Segoe UI", 12),
        ).pack(anchor="w", padx=36)

        form = tk.Frame(card, bg=COLORS["section"])
        form.pack(fill="x", padx=36, pady=(28, 0))

        self.create_login_field(form, "Nom utilisateur", self.username_var, 0)
        self.create_login_field(form, "Mot de passe", self.password_var, 1, show="*")

        tk.Label(
            form,
            textvariable=self.error_var,
            bg=COLORS["section"],
            fg="#FCA5A5",
            font=("Segoe UI", 10, "bold"),
        ).grid(row=4, column=0, sticky="w", pady=(8, 0))

        login_button = tk.Button(
            card,
            text="Se connecter",
            command=self.login,
            bg=COLORS["primary"],
            fg=COLORS["white"],
            activebackground=COLORS["primary_hover"],
            activeforeground=COLORS["white"],
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 12, "bold"),
            padx=22,
            pady=12,
        )
        login_button.pack(fill="x", padx=36, pady=(16, 0))
        login_button.bind(
            "<Enter>",
            lambda _event: login_button.configure(bg=COLORS["primary_hover"]),
        )
        login_button.bind(
            "<Leave>",
            lambda _event: login_button.configure(bg=COLORS["primary"]),
        )

        tk.Label(
            page,
            text="Cette application a ete creee par Ilyas El Bahi",
            bg=COLORS["window"],
            fg=COLORS["primary"],
            font=("Segoe UI", 12, "bold"),
        ).pack(side="bottom", pady=18)

    def create_login_field(
        self,
        parent: tk.Frame,
        label: str,
        variable: tk.StringVar,
        row: int,
        show: str | None = None,
    ) -> None:
        tk.Label(
            parent,
            text=label,
            bg=COLORS["section"],
            fg=COLORS["text"],
            font=("Segoe UI", 11, "bold"),
        ).grid(row=row * 2, column=0, sticky="w", pady=(0 if row == 0 else 14, 6))
        entry = tk.Entry(
            parent,
            textvariable=variable,
            show=show,
            bg=COLORS["input"],
            fg=COLORS["title"],
            insertbackground=COLORS["title"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["primary"],
            font=("Segoe UI", 13),
        )
        entry.grid(row=row * 2 + 1, column=0, sticky="ew", ipady=10)
        parent.columnconfigure(0, weight=1)
        if row == 0:
            entry.focus_set()

    def login(self) -> None:
        username = self.username_var.get().strip()
        password = self.password_var.get()

        if not username or not password:
            self.error_var.set("Veuillez remplir tous les champs.")
            return

        if not self.db.verify_admin_login(username, password):
            self.error_var.set("Nom utilisateur ou mot de passe incorrect.")
            self.password_var.set("")
            return

        self.root.unbind("<Return>")
        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.resizable(True, True)
        self.on_success()


class LibraryApp:
    def __init__(self, root: tk.Tk, db: DatabaseManager | None = None) -> None:
        self.root = root
        self.db = db if db is not None else DatabaseManager(DB_PATH)

        self.selected_book_id: int | None = None
        self.selected_member_id: int | None = None
        self.selected_loan_id: int | None = None
        self.book_options: dict[str, int] = {}
        self.member_options: dict[str, int] = {}
        self.language = "fr"
        self.language_var = tk.StringVar(value="FR")
        self.notifications_shown = False

        self.root.title(self.tr("app_title"))
        self.root.tk.call("tk", "scaling", 1.25)
        self.root.geometry("1920x1080")
        self.root.minsize(1280, 720)
        self.root.configure(bg=COLORS["window"])

        self.configure_style()
        self.set_window_icon()
        self.center_window(1920, 1080)
        self.create_widgets()
        self.refresh_all()
        self.root.after(700, self.show_loan_notifications)

    def tr(self, key: str) -> str:
        return TEXTS[self.language].get(key, key)

    def switch_language(self, _event=None) -> None:
        new_language = "en" if self.language_var.get() == "EN" else "fr"
        if new_language == self.language:
            return

        self.language = new_language
        self.root.title(self.tr("app_title"))
        for widget in self.root.winfo_children():
            widget.destroy()
        self.selected_book_id = None
        self.selected_member_id = None
        self.selected_loan_id = None
        self.create_widgets()
        self.refresh_all()

    def set_window_icon(self) -> None:
        try:
            if ICON_ICO_PATH.exists():
                self.root.iconbitmap(default=str(ICON_ICO_PATH))
            if ICON_PNG_PATH.exists():
                self.icon_image = tk.PhotoImage(file=str(ICON_PNG_PATH))
                self.root.iconphoto(True, self.icon_image)
        except tk.TclError:
            pass

    def center_window(self, width: int, height: int) -> None:
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def configure_style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=COLORS["window"])
        style.configure("Section.TFrame", background=COLORS["section"])
        style.configure(
            "TLabel",
            background=COLORS["window"],
            foreground=COLORS["text"],
            font=("Segoe UI", 12),
        )
        style.configure(
            "Title.TLabel",
            background=COLORS["window"],
            foreground=COLORS["title"],
            font=("Segoe UI", 26, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=COLORS["window"],
            foreground=COLORS["muted"],
            font=("Segoe UI", 13),
        )
        style.configure(
            "Credit.TLabel",
            background=COLORS["window"],
            foreground=COLORS["primary"],
            font=("Segoe UI", 13, "bold"),
        )
        style.configure(
            "TEntry",
            fieldbackground=COLORS["input"],
            background=COLORS["input"],
            foreground=COLORS["title"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            insertcolor=COLORS["title"],
            padding=(12, 10),
        )
        style.map(
            "TEntry",
            fieldbackground=[("focus", COLORS["section_alt"])],
            bordercolor=[("focus", COLORS["primary"])],
        )
        style.configure(
            "TCombobox",
            fieldbackground=COLORS["input"],
            background=COLORS["input"],
            foreground=COLORS["title"],
            arrowcolor=COLORS["text"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            padding=(12, 10),
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", COLORS["input"]), ("focus", COLORS["section_alt"])],
            foreground=[("readonly", COLORS["title"])],
            background=[("active", COLORS["section_alt"])],
            bordercolor=[("focus", COLORS["primary"])],
            arrowcolor=[("active", COLORS["white"])],
        )
        style.configure(
            "Section.TLabelframe",
            background=COLORS["section"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            relief="solid",
        )
        style.configure(
            "Section.TLabelframe.Label",
            background=COLORS["section"],
            foreground=COLORS["title"],
            font=("Segoe UI", 12, "bold"),
        )
        style.configure(
            "Treeview",
            rowheight=38,
            fieldbackground=COLORS["section"],
            background=COLORS["section"],
            foreground=COLORS["title"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            font=("Segoe UI", 12),
        )
        style.configure(
            "Treeview.Heading",
            background=COLORS["primary"],
            foreground=COLORS["white"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            font=("Segoe UI", 12, "bold"),
            padding=(12, 11),
        )
        style.map(
            "Treeview",
            background=[("selected", COLORS["selected"])],
            foreground=[("selected", COLORS["title"])],
        )
        style.map(
            "Treeview.Heading",
            background=[("active", COLORS["secondary"])],
        )
        style.configure("TNotebook", background=COLORS["window"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            padding=(30, 15),
            font=("Segoe UI", 13, "bold"),
            background=COLORS["section"],
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", COLORS["primary"])],
            foreground=[("selected", COLORS["white"])],
        )
        style.configure(
            "Vertical.TScrollbar",
            background=COLORS["secondary"],
            troughcolor=COLORS["window"],
            bordercolor=COLORS["border"],
            arrowcolor=COLORS["text"],
            lightcolor=COLORS["secondary"],
            darkcolor=COLORS["secondary"],
        )
        style.map(
            "Vertical.TScrollbar",
            background=[("active", COLORS["secondary_hover"])],
            arrowcolor=[("active", COLORS["white"])],
        )

        self.root.option_add("*TCombobox*Listbox.background", COLORS["section"])
        self.root.option_add("*TCombobox*Listbox.foreground", COLORS["title"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", COLORS["primary"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", COLORS["white"])
        self.root.option_add("*TCombobox*Listbox.font", ("Segoe UI", 12))

    def create_widgets(self) -> None:
        header = ttk.Frame(self.root, padding=(34, 26, 34, 10))
        header.pack(fill="x")

        header_left = ttk.Frame(header)
        header_left.pack(side="left", fill="x", expand=True)
        ttk.Label(
            header_left,
            text=self.tr("main_title"),
            style="Title.TLabel",
        ).pack(anchor="w")

        header_right = ttk.Frame(header)
        header_right.pack(side="right")
        ttk.Label(header_right, text=self.tr("language")).pack(anchor="e", pady=(0, 6))
        language_combo = ttk.Combobox(
            header_right,
            textvariable=self.language_var,
            values=("FR", "EN"),
            width=8,
            state="readonly",
        )
        language_combo.pack(anchor="e")
        language_combo.bind("<<ComboboxSelected>>", self.switch_language)

        footer = ttk.Frame(self.root, padding=(34, 0, 34, 18))
        footer.pack(side="bottom", fill="x")
        ttk.Label(
            footer,
            text=self.tr("credit"),
            style="Credit.TLabel",
        ).pack(anchor="e")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=34, pady=(12, 18))

        self.create_books_tab()
        self.create_members_tab()
        self.create_loans_tab()
        self.create_stats_tab()

    def make_button(
        self,
        parent: tk.Widget,
        text: str,
        command,
        variant: str = "primary",
        width: int = 14,
    ) -> tk.Button:
        if variant == "danger":
            bg = COLORS["danger"]
            active_bg = COLORS["danger_hover"]
            fg = COLORS["white"]
        elif variant == "secondary":
            bg = COLORS["secondary"]
            active_bg = COLORS["secondary_hover"]
            fg = COLORS["title"]
        else:
            bg = COLORS["primary"]
            active_bg = COLORS["primary_hover"]
            fg = COLORS["white"]

        button = tk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            bg=bg,
            fg=fg,
            activebackground=active_bg,
            activeforeground=fg,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["primary"],
            cursor="hand2",
            font=("Segoe UI", 11, "bold"),
            padx=14,
            pady=11,
        )
        button.bind("<Enter>", lambda _event: button.configure(bg=active_bg))
        button.bind("<Leave>", lambda _event: button.configure(bg=bg))
        return button

    def create_books_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=22)
        self.notebook.add(tab, text=self.tr("books_tab"))
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(0, weight=1)

        form = ttk.LabelFrame(tab, text=self.tr("book_form"), style="Section.TLabelframe")
        form.grid(row=0, column=0, sticky="ns", padx=(0, 14))

        self.book_vars = {
            "titre": tk.StringVar(),
            "auteur": tk.StringVar(),
            "genre": tk.StringVar(),
            "annee": tk.StringVar(),
            "total": tk.StringVar(value="1"),
        }
        fields = [
            (self.tr("title"), "titre"),
            (self.tr("author"), "auteur"),
            (self.tr("genre"), "genre"),
            (self.tr("year"), "annee"),
            (self.tr("copies"), "total"),
        ]
        for row, (label, key) in enumerate(fields):
            ttk.Label(form, text=label, background=COLORS["section"]).grid(
                row=row,
                column=0,
                sticky="w",
                padx=12,
                pady=(12 if row == 0 else 6, 4),
            )
            ttk.Entry(form, textvariable=self.book_vars[key], width=36).grid(
                row=row,
                column=1,
                sticky="ew",
                padx=(0, 12),
                pady=(12 if row == 0 else 6, 4),
            )

        buttons = ttk.Frame(form, style="Section.TFrame")
        buttons.grid(row=len(fields), column=0, columnspan=2, padx=12, pady=16)
        self.make_button(buttons, self.tr("add"), self.add_book).grid(row=0, column=0, padx=3)
        self.make_button(buttons, self.tr("edit"), self.update_book).grid(row=0, column=1, padx=3)
        self.make_button(buttons, self.tr("delete"), self.delete_book, "danger").grid(
            row=1, column=0, padx=3, pady=(7, 0)
        )
        self.make_button(buttons, self.tr("clear"), self.clear_book_form, "secondary").grid(
            row=1, column=1, padx=3, pady=(7, 0)
        )

        content = ttk.Frame(tab)
        content.grid(row=0, column=1, sticky="nsew")
        content.rowconfigure(1, weight=1)
        content.columnconfigure(0, weight=1)

        search = ttk.Frame(content)
        search.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        search.columnconfigure(1, weight=1)
        ttk.Label(search, text=self.tr("book_search")).grid(row=0, column=0, padx=(0, 8))
        self.book_search_var = tk.StringVar()
        ttk.Entry(search, textvariable=self.book_search_var).grid(row=0, column=1, sticky="ew")
        self.make_button(search, self.tr("search"), self.refresh_books, width=12).grid(
            row=0, column=2, padx=8
        )
        self.make_button(search, self.tr("refresh"), self.clear_book_search, "secondary", 12).grid(
            row=0, column=3
        )

        columns = ("titre", "auteur", "genre", "annee", "total", "dispo")
        self.books_tree = ttk.Treeview(
            content,
            columns=columns,
            show="headings",
            height=18,
        )
        headings = {
            "titre": self.tr("title"),
            "auteur": self.tr("author"),
            "genre": self.tr("genre"),
            "annee": self.tr("year"),
            "total": self.tr("total"),
            "dispo": self.tr("available"),
        }
        widths = {
            "titre": 310,
            "auteur": 260,
            "genre": 190,
            "annee": 110,
            "total": 120,
            "dispo": 150,
        }
        for column in columns:
            self.books_tree.heading(column, text=headings[column])
            self.books_tree.column(column, width=widths[column], anchor="w")

        self.books_tree.grid(row=1, column=0, sticky="nsew")
        self.books_tree.bind("<<TreeviewSelect>>", self.on_book_selected)
        self.add_scrollbar(content, self.books_tree, row=1, column=1)

    def create_members_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=22)
        self.notebook.add(tab, text=self.tr("members_tab"))
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(0, weight=1)

        form = ttk.LabelFrame(tab, text=self.tr("member_form"), style="Section.TLabelframe")
        form.grid(row=0, column=0, sticky="ns", padx=(0, 14))

        self.member_vars = {
            "nom": tk.StringVar(),
            "prenom": tk.StringVar(),
            "email": tk.StringVar(),
            "numero": tk.StringVar(),
        }
        fields = [
            (self.tr("name"), "nom"),
            (self.tr("first_name"), "prenom"),
            (self.tr("email"), "email"),
            (self.tr("member_number"), "numero"),
        ]
        for row, (label, key) in enumerate(fields):
            ttk.Label(form, text=label, background=COLORS["section"]).grid(
                row=row,
                column=0,
                sticky="w",
                padx=12,
                pady=(12 if row == 0 else 6, 4),
            )
            ttk.Entry(form, textvariable=self.member_vars[key], width=36).grid(
                row=row,
                column=1,
                sticky="ew",
                padx=(0, 12),
                pady=(12 if row == 0 else 6, 4),
            )

        buttons = ttk.Frame(form, style="Section.TFrame")
        buttons.grid(row=len(fields), column=0, columnspan=2, padx=12, pady=16)
        self.make_button(buttons, self.tr("add"), self.add_member).grid(row=0, column=0, padx=3)
        self.make_button(buttons, self.tr("edit"), self.update_member).grid(row=0, column=1, padx=3)
        self.make_button(buttons, self.tr("delete"), self.delete_member, "danger").grid(
            row=1,
            column=0,
            padx=3,
            pady=(7, 0),
        )
        self.make_button(buttons, self.tr("clear"), self.clear_member_form, "secondary").grid(
            row=1,
            column=1,
            padx=3,
            pady=(7, 0),
        )

        content = ttk.Frame(tab)
        content.grid(row=0, column=1, sticky="nsew")
        content.rowconfigure(1, weight=1)
        content.columnconfigure(0, weight=1)

        search = ttk.Frame(content)
        search.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        search.columnconfigure(1, weight=1)
        ttk.Label(search, text=self.tr("member_search")).grid(row=0, column=0, padx=(0, 8))
        self.member_search_var = tk.StringVar()
        ttk.Entry(search, textvariable=self.member_search_var).grid(
            row=0,
            column=1,
            sticky="ew",
        )
        self.make_button(search, self.tr("search"), self.refresh_members, width=12).grid(
            row=0,
            column=2,
            padx=8,
        )
        self.make_button(search, self.tr("refresh"), self.clear_member_search, "secondary", 12).grid(
            row=0,
            column=3,
        )

        columns = ("nom", "prenom", "email", "numero")
        self.members_tree = ttk.Treeview(
            content,
            columns=columns,
            show="headings",
            height=18,
        )
        headings = {
            "nom": self.tr("name"),
            "prenom": self.tr("first_name"),
            "email": self.tr("email"),
            "numero": self.tr("member_number"),
        }
        widths = {
            "nom": 210,
            "prenom": 210,
            "email": 360,
            "numero": 230,
        }
        for column in columns:
            self.members_tree.heading(column, text=headings[column])
            self.members_tree.column(column, width=widths[column], anchor="w")

        self.members_tree.grid(row=1, column=0, sticky="nsew")
        self.members_tree.bind("<<TreeviewSelect>>", self.on_member_selected)
        self.add_scrollbar(content, self.members_tree, row=1, column=1)

    def create_loans_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=22)
        self.notebook.add(tab, text=self.tr("loans_tab"))
        tab.rowconfigure(2, weight=1)
        tab.columnconfigure(0, weight=1)

        form = ttk.LabelFrame(tab, text=self.tr("new_loan"), style="Section.TLabelframe")
        form.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        ttk.Label(form, text=self.tr("book"), background=COLORS["section"]).grid(
            row=0,
            column=0,
            sticky="w",
            padx=12,
            pady=12,
        )
        self.loan_book_var = tk.StringVar()
        self.loan_book_combo = ttk.Combobox(
            form,
            textvariable=self.loan_book_var,
            state="readonly",
        )
        self.loan_book_combo.grid(row=0, column=1, sticky="ew", pady=12, padx=(0, 12))

        ttk.Label(form, text=self.tr("member"), background=COLORS["section"]).grid(
            row=0,
            column=2,
            sticky="w",
            padx=12,
            pady=12,
        )
        self.loan_member_var = tk.StringVar()
        self.loan_member_combo = ttk.Combobox(
            form,
            textvariable=self.loan_member_var,
            state="readonly",
        )
        self.loan_member_combo.grid(row=0, column=3, sticky="ew", pady=12, padx=(0, 12))

        actions = ttk.Frame(form, style="Section.TFrame")
        actions.grid(row=0, column=4, padx=12, pady=12)
        self.make_button(actions, self.tr("borrow"), self.add_loan, width=13).grid(
            row=0,
            column=0,
            padx=3,
        )
        self.make_button(actions, self.tr("return_book"), self.return_loan, width=13).grid(
            row=0,
            column=1,
            padx=3,
        )

        search = ttk.Frame(tab)
        search.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        search.columnconfigure(1, weight=1)
        ttk.Label(search, text=self.tr("loan_search")).grid(row=0, column=0, padx=(0, 8))
        self.loan_search_var = tk.StringVar()
        ttk.Entry(search, textvariable=self.loan_search_var).grid(
            row=0,
            column=1,
            sticky="ew",
        )
        self.make_button(search, self.tr("search"), self.refresh_loans, width=12).grid(
            row=0,
            column=2,
            padx=8,
        )
        self.make_button(search, self.tr("refresh"), self.clear_loan_search, "secondary", 12).grid(
            row=0,
            column=3,
        )

        table_frame = ttk.Frame(tab)
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        columns = ("livre", "membre", "numero", "date_emprunt", "date_retour", "statut", "penalite")
        self.loans_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=18,
        )
        headings = {
            "livre": self.tr("book"),
            "membre": self.tr("member"),
            "numero": self.tr("member_number"),
            "date_emprunt": self.tr("loan_date"),
            "date_retour": self.tr("due_date"),
            "statut": self.tr("status"),
            "penalite": self.tr("penalty"),
        }
        widths = {
            "livre": 360,
            "membre": 270,
            "numero": 190,
            "date_emprunt": 160,
            "date_retour": 160,
            "statut": 190,
            "penalite": 140,
        }
        for column in columns:
            self.loans_tree.heading(column, text=headings[column])
            self.loans_tree.column(column, width=widths[column], anchor="w")

        self.loans_tree.tag_configure("late", foreground=COLORS["danger"])
        self.loans_tree.tag_configure("soon", foreground=COLORS["primary_hover"])

        self.loans_tree.grid(row=0, column=0, sticky="nsew")
        self.loans_tree.bind("<<TreeviewSelect>>", self.on_loan_selected)
        self.add_scrollbar(table_frame, self.loans_tree, row=0, column=1)

    def create_stats_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=22)
        self.notebook.add(tab, text=self.tr("stats_tab"))
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)

        summary = ttk.Frame(tab)
        summary.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        for column in range(5):
            summary.columnconfigure(column, weight=1)

        self.stats_vars = {
            "total_books": tk.StringVar(value="0"),
            "available": tk.StringVar(value="0"),
            "members": tk.StringVar(value="0"),
            "active_loans": tk.StringVar(value="0"),
            "overdue_loans": tk.StringVar(value="0"),
        }
        cards = [
            (self.tr("stock_books"), "total_books"),
            (self.tr("available_copies"), "available"),
            (self.tr("members_tab"), "members"),
            (self.tr("active_loans"), "active_loans"),
            (self.tr("overdue_loans"), "overdue_loans"),
        ]
        for column, (title, key) in enumerate(cards):
            card = ttk.Frame(summary, style="Section.TFrame", padding=24)
            card.grid(row=0, column=column, sticky="ew", padx=6)
            ttk.Label(
                card,
                text=title,
                background=COLORS["section"],
                foreground=COLORS["text"],
                font=("Segoe UI", 12),
            ).pack(anchor="w")
            ttk.Label(
                card,
                textvariable=self.stats_vars[key],
                background=COLORS["section"],
                foreground=COLORS["primary"],
                font=("Segoe UI", 34, "bold"),
            ).pack(anchor="w", pady=(4, 0))

        most = ttk.LabelFrame(
            tab,
            text=self.tr("most_borrowed"),
            style="Section.TLabelframe",
        )
        most.grid(row=1, column=0, sticky="nsew")
        most.rowconfigure(0, weight=1)
        most.columnconfigure(0, weight=1)

        columns = ("titre", "auteur", "emprunts")
        self.stats_tree = ttk.Treeview(most, columns=columns, show="headings", height=14)
        self.stats_tree.heading("titre", text=self.tr("title"))
        self.stats_tree.heading("auteur", text=self.tr("author"))
        self.stats_tree.heading("emprunts", text=self.tr("loan_count"))
        self.stats_tree.column("titre", width=520, anchor="w")
        self.stats_tree.column("auteur", width=360, anchor="w")
        self.stats_tree.column("emprunts", width=240, anchor="center")
        self.stats_tree.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.add_scrollbar(most, self.stats_tree, row=0, column=1, pady=12)

        actions = ttk.Frame(tab)
        actions.grid(row=2, column=0, sticky="e", pady=(14, 0))
        self.make_button(actions, self.tr("export_report_pdf"), self.export_report_pdf, width=18).grid(
            row=0,
            column=0,
            padx=6,
        )
        self.make_button(actions, self.tr("export_late_pdf"), self.export_overdue_pdf, "secondary", 18).grid(
            row=0,
            column=1,
            padx=6,
        )
        self.make_button(actions, self.tr("export_report"), self.export_report_csv, "secondary", 18).grid(
            row=1,
            column=0,
            padx=6,
            pady=(8, 0),
        )
        self.make_button(actions, self.tr("export_late"), self.export_overdue_csv, "secondary", 18).grid(
            row=1,
            column=1,
            padx=6,
            pady=(8, 0),
        )

    def add_scrollbar(
        self,
        parent: tk.Widget,
        tree: ttk.Treeview,
        row: int,
        column: int,
        pady: int | tuple[int, int] = 0,
    ) -> None:
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=row, column=column, sticky="ns", pady=pady)

    def refresh_all(self) -> None:
        self.refresh_books()
        self.refresh_members()
        self.refresh_combos()
        self.refresh_loans()
        self.refresh_stats()

    def refresh_books(self) -> None:
        for item in self.books_tree.get_children():
            self.books_tree.delete(item)

        for book in self.db.list_books(self.book_search_var.get()):
            self.books_tree.insert(
                "",
                "end",
                iid=str(book["id"]),
                values=(
                    book["titre"],
                    book["auteur"],
                    book["genre"] or "",
                    book["annee"] or "",
                    book["total_exemplaires"],
                    book["exemplaires_disponibles"],
                ),
            )

    def refresh_members(self) -> None:
        for item in self.members_tree.get_children():
            self.members_tree.delete(item)

        for member in self.db.list_members(self.member_search_var.get()):
            self.members_tree.insert(
                "",
                "end",
                iid=str(member["id"]),
                values=(
                    member["nom"],
                    member["prenom"],
                    member["email"] or "",
                    member["numero_adhesion"],
                ),
            )

    def refresh_combos(self) -> None:
        self.book_options.clear()
        for book in self.db.list_books():
            label = (
                f"{book['id']} - {book['titre']} "
                f"({book['exemplaires_disponibles']}/{book['total_exemplaires']})"
            )
            self.book_options[label] = int(book["id"])
        self.loan_book_combo["values"] = list(self.book_options.keys())

        self.member_options.clear()
        for member in self.db.list_members():
            label = (
                f"{member['id']} - {member['prenom']} {member['nom']} "
                f"[{member['numero_adhesion']}]"
            )
            self.member_options[label] = int(member["id"])
        self.loan_member_combo["values"] = list(self.member_options.keys())

    def loan_status_and_penalty(self, due_date_text: str) -> tuple[str, str, str]:
        today = date.today()
        due_date = parse_iso_date(due_date_text)
        days_late = (today - due_date).days

        if days_late > 0:
            return (
                f"{self.tr('status_late')} ({days_late} j)",
                f"{days_late * FINE_PER_DAY} DH",
                "late",
            )

        days_left = (due_date - today).days
        if days_left <= RETURN_SOON_DAYS:
            return (self.tr("status_due_soon"), "0 DH", "soon")

        return (self.tr("status_ok"), "0 DH", "")

    def refresh_loans(self) -> None:
        for item in self.loans_tree.get_children():
            self.loans_tree.delete(item)

        for loan in self.db.list_active_loans(self.loan_search_var.get()):
            status, penalty, tag = self.loan_status_and_penalty(loan["date_retour_prevue"])
            self.loans_tree.insert(
                "",
                "end",
                iid=str(loan["id"]),
                values=(
                    f"{loan['livre_titre']} - {loan['livre_auteur']}",
                    f"{loan['membre_prenom']} {loan['membre_nom']}",
                    loan["numero_adhesion"],
                    loan["date_emprunt"],
                    loan["date_retour_prevue"],
                    status,
                    penalty,
                ),
                tags=(tag,) if tag else (),
            )

    def refresh_stats(self) -> None:
        stats = self.db.get_statistics()
        for key, value in stats.items():
            self.stats_vars[key].set(str(value))

        for item in self.stats_tree.get_children():
            self.stats_tree.delete(item)

        for index, row in enumerate(self.db.list_most_borrowed_books(), start=1):
            self.stats_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(row["titre"], row["auteur"], row["emprunts"]),
            )

    def show_loan_notifications(self) -> None:
        if self.notifications_shown:
            return

        self.notifications_shown = True
        alerts = self.db.get_loan_alert_counts()
        if alerts["overdue"] == 0 and alerts["due_soon"] == 0:
            return

        message = (
            f"Retards: {alerts['overdue']}\n"
            f"Retours imminents ({RETURN_SOON_DAYS} jours): {alerts['due_soon']}\n\n"
            f"Penalite appliquee: {FINE_PER_DAY} DH par jour de retard."
        )
        messagebox.showwarning("Notifications emprunts", message)

    def ask_csv_path(self, default_name: str) -> str:
        return filedialog.asksaveasfilename(
            title="Enregistrer le fichier CSV",
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=(("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")),
        )

    def ask_pdf_path(self, default_name: str) -> str:
        RESULT_DIR.mkdir(exist_ok=True)
        selected_path = filedialog.asksaveasfilename(
            title="Enregistrer le fichier PDF",
            defaultextension=".pdf",
            initialdir=str(RESULT_DIR),
            initialfile=default_name,
            filetypes=(("Fichiers PDF", "*.pdf"), ("Tous les fichiers", "*.*")),
        )
        if not selected_path:
            return ""
        return str(RESULT_DIR / Path(selected_path).name)

    def build_pdf_loan_rows(self) -> list[list[str]]:
        rows = []
        for loan in self.db.list_all_loans():
            if loan["date_retour_reelle"]:
                status = "Rendu"
                penalty = "0 DH"
            else:
                status, penalty, _tag = self.loan_status_and_penalty(loan["date_retour_prevue"])
            rows.append(
                [
                    loan["livre_titre"],
                    loan["livre_auteur"],
                    f"{loan['membre_prenom']} {loan['membre_nom']}",
                    loan["numero_adhesion"],
                    loan["date_emprunt"],
                    loan["date_retour_prevue"],
                    loan["date_retour_reelle"] or "-",
                    status,
                    penalty,
                ]
            )
        return rows

    def export_report_pdf(self) -> None:
        path = self.ask_pdf_path(f"rapport_bibliotheque_{date.today().isoformat()}.pdf")
        if not path:
            return

        stats = self.db.get_statistics()
        pdf = PdfReport(
            path,
            "Rapport bibliotheque",
            f"Genere le {date.today().isoformat()} - Application creee par Ilyas El Bahi",
        )
        pdf.add_kpis(
            [
                ("Livres en stock", stats["total_books"]),
                ("Disponibles", stats["available"]),
                ("Membres", stats["members"]),
                ("Emprunts actifs", stats["active_loans"]),
                ("Retards", stats["overdue_loans"]),
            ],
            danger_index=4,
        )
        pdf.add_table(
            "Livres",
            ["Titre", "Auteur", "Genre", "Annee", "Total", "Dispo"],
            [
                [
                    book["titre"],
                    book["auteur"],
                    book["genre"] or "",
                    book["annee"] or "",
                    book["total_exemplaires"],
                    book["exemplaires_disponibles"],
                ]
                for book in self.db.list_books()
            ],
            [135, 100, 90, 55, 45, 70],
        )
        pdf.add_table(
            "Membres",
            ["Nom", "Prenom", "Email", "Adhesion"],
            [
                [
                    member["nom"],
                    member["prenom"],
                    member["email"] or "",
                    member["numero_adhesion"],
                ]
                for member in self.db.list_members()
            ],
            [100, 90, 190, 100],
        )
        pdf.add_table(
            "Emprunts",
            [
                "Livre",
                "Auteur",
                "Membre",
                "Adhesion",
                "Emprunt",
                "Prevu",
                "Retour",
                "Statut",
                "Pen.",
            ],
            self.build_pdf_loan_rows(),
            [85, 56, 70, 58, 53, 53, 53, 46, 35],
        )

        try:
            pdf.save()
        except OSError as error:
            messagebox.showerror("Erreur", f"Export PDF impossible: {error}")
            return

        messagebox.showinfo("Succes", "Rapport PDF exporte avec succes.")

    def export_overdue_pdf(self) -> None:
        path = self.ask_pdf_path(f"retards_bibliotheque_{date.today().isoformat()}.pdf")
        if not path:
            return

        overdue_rows = []
        for loan in self.db.list_overdue_loans():
            due_date = parse_iso_date(loan["date_retour_prevue"])
            days_late = (date.today() - due_date).days
            overdue_rows.append(
                [
                    loan["livre_titre"],
                    loan["livre_auteur"],
                    f"{loan['membre_prenom']} {loan['membre_nom']}",
                    loan["numero_adhesion"],
                    loan["date_emprunt"],
                    loan["date_retour_prevue"],
                    days_late,
                    f"{days_late * FINE_PER_DAY} DH",
                ]
            )

        pdf = PdfReport(
            path,
            "Rapport des retards",
            f"Penalite: {FINE_PER_DAY} DH par jour - Genere le {date.today().isoformat()}",
        )
        pdf.add_kpis(
            [
                ("Retards", len(overdue_rows)),
                ("Penalite / jour", f"{FINE_PER_DAY} DH"),
                ("Date rapport", date.today().isoformat()),
            ],
            danger_index=0,
        )
        pdf.add_table(
            "Emprunts en retard",
            ["Livre", "Auteur", "Membre", "Adhesion", "Emprunt", "Prevu", "Jours", "Penalite"],
            overdue_rows,
            [85, 60, 75, 58, 55, 55, 45, 50],
        )

        try:
            pdf.save()
        except OSError as error:
            messagebox.showerror("Erreur", f"Export PDF impossible: {error}")
            return

        messagebox.showinfo("Succes", "Rapport PDF des retards exporte avec succes.")

    def export_report_csv(self) -> None:
        path = self.ask_csv_path(f"rapport_bibliotheque_{date.today().isoformat()}.csv")
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file, delimiter=";")
                writer.writerow(["Rapport bibliotheque"])
                writer.writerow(["Date", date.today().isoformat()])
                writer.writerow([])

                writer.writerow(["Livres"])
                writer.writerow(["Titre", "Auteur", "Genre", "Annee", "Total", "Disponibles"])
                for book in self.db.list_books():
                    writer.writerow(
                        [
                            book["titre"],
                            book["auteur"],
                            book["genre"] or "",
                            book["annee"] or "",
                            book["total_exemplaires"],
                            book["exemplaires_disponibles"],
                        ]
                    )
                writer.writerow([])

                writer.writerow(["Membres"])
                writer.writerow(["Nom", "Prenom", "Email", "Numero adhesion"])
                for member in self.db.list_members():
                    writer.writerow(
                        [
                            member["nom"],
                            member["prenom"],
                            member["email"] or "",
                            member["numero_adhesion"],
                        ]
                    )
                writer.writerow([])

                writer.writerow(["Emprunts"])
                writer.writerow(
                    [
                        "Livre",
                        "Auteur",
                        "Membre",
                        "Numero adhesion",
                        "Date emprunt",
                        "Retour prevu",
                        "Retour reel",
                        "Statut",
                        "Penalite",
                    ]
                )
                for loan in self.db.list_all_loans():
                    if loan["date_retour_reelle"]:
                        status = "Rendu"
                        penalty = "0 DH"
                    else:
                        status, penalty, _tag = self.loan_status_and_penalty(
                            loan["date_retour_prevue"]
                        )
                    writer.writerow(
                        [
                            loan["livre_titre"],
                            loan["livre_auteur"],
                            f"{loan['membre_prenom']} {loan['membre_nom']}",
                            loan["numero_adhesion"],
                            loan["date_emprunt"],
                            loan["date_retour_prevue"],
                            loan["date_retour_reelle"] or "",
                            status,
                            penalty,
                        ]
                    )
        except OSError as error:
            messagebox.showerror("Erreur", f"Export impossible: {error}")
            return

        messagebox.showinfo("Succes", "Rapport CSV exporte avec succes.")

    def export_overdue_csv(self) -> None:
        path = self.ask_csv_path(f"retards_bibliotheque_{date.today().isoformat()}.csv")
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file, delimiter=";")
                writer.writerow(["Retards bibliotheque"])
                writer.writerow(["Penalite par jour", f"{FINE_PER_DAY} DH"])
                writer.writerow([])
                writer.writerow(
                    [
                        "Livre",
                        "Auteur",
                        "Membre",
                        "Numero adhesion",
                        "Date emprunt",
                        "Retour prevu",
                        "Jours retard",
                        "Penalite",
                    ]
                )
                for loan in self.db.list_overdue_loans():
                    due_date = parse_iso_date(loan["date_retour_prevue"])
                    days_late = (date.today() - due_date).days
                    writer.writerow(
                        [
                            loan["livre_titre"],
                            loan["livre_auteur"],
                            f"{loan['membre_prenom']} {loan['membre_nom']}",
                            loan["numero_adhesion"],
                            loan["date_emprunt"],
                            loan["date_retour_prevue"],
                            days_late,
                            f"{days_late * FINE_PER_DAY} DH",
                        ]
                    )
        except OSError as error:
            messagebox.showerror("Erreur", f"Export impossible: {error}")
            return

        messagebox.showinfo("Succes", "Liste des retards exportee avec succes.")

    def on_book_selected(self, _event=None) -> None:
        selection = self.books_tree.selection()
        if not selection:
            return

        self.selected_book_id = int(selection[0])
        book = self.db.get_book(self.selected_book_id)
        if book is None:
            return

        self.book_vars["titre"].set(book["titre"])
        self.book_vars["auteur"].set(book["auteur"])
        self.book_vars["genre"].set(book["genre"] or "")
        self.book_vars["annee"].set("" if book["annee"] is None else str(book["annee"]))
        self.book_vars["total"].set(str(book["total_exemplaires"]))

    def on_member_selected(self, _event=None) -> None:
        selection = self.members_tree.selection()
        if not selection:
            return

        self.selected_member_id = int(selection[0])
        member = self.db.get_member(self.selected_member_id)
        if member is None:
            return

        self.member_vars["nom"].set(member["nom"])
        self.member_vars["prenom"].set(member["prenom"])
        self.member_vars["email"].set(member["email"] or "")
        self.member_vars["numero"].set(member["numero_adhesion"])

    def on_loan_selected(self, _event=None) -> None:
        selection = self.loans_tree.selection()
        if selection:
            self.selected_loan_id = int(selection[0])

    def add_book(self) -> None:
        data = self.read_book_form()
        if data is None:
            return

        try:
            self.db.add_book(**data)
        except Exception as error:
            messagebox.showerror("Erreur", str(error))
            return

        self.clear_book_form()
        self.refresh_all()
        messagebox.showinfo("Succes", "Livre ajoute avec succes.")

    def update_book(self) -> None:
        if self.selected_book_id is None:
            messagebox.showwarning("Selection", "Selectionnez un livre a modifier.")
            return

        data = self.read_book_form()
        if data is None:
            return

        try:
            self.db.update_book(self.selected_book_id, **data)
        except Exception as error:
            messagebox.showerror("Erreur", str(error))
            return

        self.clear_book_form()
        self.refresh_all()
        messagebox.showinfo("Succes", "Livre modifie avec succes.")

    def delete_book(self) -> None:
        if self.selected_book_id is None:
            messagebox.showwarning("Selection", "Selectionnez un livre a supprimer.")
            return

        confirmed = messagebox.askyesno(
            "Confirmation",
            "Voulez-vous vraiment supprimer ce livre ?",
        )
        if not confirmed:
            return

        try:
            self.db.delete_book(self.selected_book_id)
        except Exception as error:
            messagebox.showerror("Erreur", str(error))
            return

        self.clear_book_form()
        self.refresh_all()
        messagebox.showinfo("Succes", "Livre supprime avec succes.")

    def read_book_form(self) -> dict[str, object] | None:
        titre = self.book_vars["titre"].get().strip()
        auteur = self.book_vars["auteur"].get().strip()
        genre = self.book_vars["genre"].get().strip()
        annee_text = self.book_vars["annee"].get().strip()
        total_text = self.book_vars["total"].get().strip()

        if not titre or not auteur:
            messagebox.showwarning("Validation", "Le titre et l'auteur sont obligatoires.")
            return None

        annee: int | None = None
        if annee_text:
            try:
                annee = int(annee_text)
            except ValueError:
                messagebox.showwarning("Validation", "L'annee doit etre un nombre.")
                return None

        try:
            total = int(total_text)
        except ValueError:
            messagebox.showwarning("Validation", "Le nombre d'exemplaires doit etre entier.")
            return None

        if total < 0:
            messagebox.showwarning(
                "Validation",
                "Le nombre d'exemplaires ne peut pas etre negatif.",
            )
            return None

        return {
            "titre": titre,
            "auteur": auteur,
            "genre": genre,
            "annee": annee,
            "total_exemplaires": total,
        }

    def clear_book_form(self) -> None:
        for variable in self.book_vars.values():
            variable.set("")
        self.book_vars["total"].set("1")
        self.selected_book_id = None
        self.books_tree.selection_remove(self.books_tree.selection())

    def clear_book_search(self) -> None:
        self.book_search_var.set("")
        self.refresh_books()

    def add_member(self) -> None:
        data = self.read_member_form()
        if data is None:
            return

        try:
            self.db.add_member(**data)
        except sqlite3.IntegrityError:
            messagebox.showerror("Erreur", "Ce numero d'adhesion existe deja.")
            return
        except Exception as error:
            messagebox.showerror("Erreur", str(error))
            return

        self.clear_member_form()
        self.refresh_all()
        messagebox.showinfo("Succes", "Membre ajoute avec succes.")

    def update_member(self) -> None:
        if self.selected_member_id is None:
            messagebox.showwarning("Selection", "Selectionnez un membre a modifier.")
            return

        data = self.read_member_form()
        if data is None:
            return

        try:
            self.db.update_member(self.selected_member_id, **data)
        except sqlite3.IntegrityError:
            messagebox.showerror("Erreur", "Ce numero d'adhesion existe deja.")
            return
        except Exception as error:
            messagebox.showerror("Erreur", str(error))
            return

        self.clear_member_form()
        self.refresh_all()
        messagebox.showinfo("Succes", "Membre modifie avec succes.")

    def delete_member(self) -> None:
        if self.selected_member_id is None:
            messagebox.showwarning("Selection", "Selectionnez un membre a supprimer.")
            return

        confirmed = messagebox.askyesno(
            "Confirmation",
            "Voulez-vous vraiment supprimer ce membre ?",
        )
        if not confirmed:
            return

        try:
            self.db.delete_member(self.selected_member_id)
        except Exception as error:
            messagebox.showerror("Erreur", str(error))
            return

        self.clear_member_form()
        self.refresh_all()
        messagebox.showinfo("Succes", "Membre supprime avec succes.")

    def read_member_form(self) -> dict[str, str] | None:
        nom = self.member_vars["nom"].get().strip()
        prenom = self.member_vars["prenom"].get().strip()
        email = self.member_vars["email"].get().strip()
        numero = self.member_vars["numero"].get().strip()

        if not nom or not prenom or not numero:
            messagebox.showwarning(
                "Validation",
                "Le nom, le prenom et le numero d'adhesion sont obligatoires.",
            )
            return None

        return {
            "nom": nom,
            "prenom": prenom,
            "email": email,
            "numero_adhesion": numero,
        }

    def clear_member_form(self) -> None:
        for variable in self.member_vars.values():
            variable.set("")
        self.selected_member_id = None
        self.members_tree.selection_remove(self.members_tree.selection())

    def clear_member_search(self) -> None:
        self.member_search_var.set("")
        self.refresh_members()

    def add_loan(self) -> None:
        book_label = self.loan_book_var.get()
        member_label = self.loan_member_var.get()
        book_id = self.book_options.get(book_label)
        member_id = self.member_options.get(member_label)

        if book_id is None or member_id is None:
            messagebox.showwarning(
                "Validation",
                "Selectionnez un livre et un membre.",
            )
            return

        try:
            self.db.add_loan(book_id, member_id)
        except Exception as error:
            messagebox.showerror("Erreur", str(error))
            return

        self.loan_book_var.set("")
        self.loan_member_var.set("")
        self.refresh_all()
        messagebox.showinfo("Succes", "Emprunt enregistre avec succes.")

    def return_loan(self) -> None:
        if self.selected_loan_id is None:
            messagebox.showwarning(
                "Selection",
                "Selectionnez un emprunt en cours a retourner.",
            )
            return

        confirmed = messagebox.askyesno(
            "Confirmation",
            "Confirmer le retour de ce livre ?",
        )
        if not confirmed:
            return

        try:
            self.db.return_loan(self.selected_loan_id)
        except Exception as error:
            messagebox.showerror("Erreur", str(error))
            return

        self.selected_loan_id = None
        self.refresh_all()
        messagebox.showinfo("Succes", "Retour enregistre avec succes.")

    def clear_loan_search(self) -> None:
        self.loan_search_var.set("")
        self.refresh_loans()


def main() -> None:
    root = tk.Tk()
    db = DatabaseManager(DB_PATH)
    LoginWindow(root, db, lambda: LibraryApp(root, db))
    root.mainloop()


if __name__ == "__main__":
    main()
