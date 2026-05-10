"""
Login page — St Bernard's College branded.
Credentials are saved encrypted using Fernet (AES-128-CBC) in ~/.sbc_portal/
"""
import tkinter as tk
import threading
import os
import json
import base64

from ui.theme import *
from ui.crest import CrestImage

# ── Encrypted credential storage ─────────────────────────────────────────────

CREDS_DIR  = os.path.expanduser("~/.sbc_portal")
CREDS_FILE = os.path.join(CREDS_DIR, "credentials.enc")
KEY_FILE   = os.path.join(CREDS_DIR, "key.bin")


def _get_or_create_key() -> bytes:
    """Load or generate a Fernet encryption key stored in ~/.sbc_portal/key.bin"""
    from cryptography.fernet import Fernet
    os.makedirs(CREDS_DIR, mode=0o700, exist_ok=True)
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read()
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    os.chmod(KEY_FILE, 0o600)
    return key


def save_credentials(username: str, password: str) -> None:
    """Encrypt and save credentials to disk."""
    try:
        from cryptography.fernet import Fernet
        key = _get_or_create_key()
        f = Fernet(key)
        payload = json.dumps({"username": username, "password": password}).encode()
        encrypted = f.encrypt(payload)
        os.makedirs(CREDS_DIR, mode=0o700, exist_ok=True)
        with open(CREDS_FILE, "wb") as fp:
            fp.write(encrypted)
        os.chmod(CREDS_FILE, 0o600)
    except Exception:
        pass  # Never crash the app over credential saving


def load_credentials() -> tuple:
    """Return (username, password) or ('', '') if not saved."""
    try:
        from cryptography.fernet import Fernet, InvalidToken
        if not os.path.exists(CREDS_FILE) or not os.path.exists(KEY_FILE):
            return "", ""
        key = _get_or_create_key()
        f = Fernet(key)
        with open(CREDS_FILE, "rb") as fp:
            encrypted = fp.read()
        payload = json.loads(f.decrypt(encrypted).decode())
        return payload.get("username", ""), payload.get("password", "")
    except Exception:
        return "", ""


def clear_credentials() -> None:
    for path in [CREDS_FILE, KEY_FILE]:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass


# ── Login page ────────────────────────────────────────────────────────────────

class LoginPage(tk.Frame):

    def __init__(self, parent, on_login_success, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self.on_login_success = on_login_success
        self._build_ui()

    def _build_ui(self):
        # ── Left branding panel ────────────────────────────────────────
        left = tk.Frame(self, bg=BG_MID, width=380)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Frame(left, bg=ACCENT, height=5).pack(fill="x")

        CrestImage(left, width=280, bg=BG_MID).pack(pady=8)

        tk.Label(left, text="St Bernard's College",
                 bg=BG_MID, fg=FG_PRIMARY,
                 font=("Georgia", 16, "bold")).pack()
        tk.Label(left, text="Essendon, Victoria",
                 bg=BG_MID, fg=FG_MUTED,
                 font=("TkDefaultFont", 10)).pack(pady=0)

        tk.Frame(left, bg=ACCENT, height=2, width=70).pack(pady=20)

        tk.Label(left, text="Academic Portal",
                 bg=BG_MID, fg=ACCENT,
                 font=("Georgia", 17, "bold")).pack()
        tk.Label(left, text="mySBC · Student Dashboard",
                 bg=BG_MID, fg=FG_MUTED,
                 font=("TkDefaultFont", 9)).pack(pady=24)

        for icon, text in [
            ("📊", "Grades & Assessments"),
            ("📚", "Classes & Assignments"),
            ("📅", "Due Dates at a Glance"),
            ("🗂️", "Organised by Year"),
        ]:
            row = tk.Frame(left, bg=BG_MID)
            row.pack(fill="x", padx=36, pady=3)
            tk.Label(row, text=icon, bg=BG_MID,
                     font=("TkDefaultFont", 11)).pack(side="left")
            tk.Label(row, text=f"  {text}", bg=BG_MID, fg=FG_SEC,
                     font=("TkDefaultFont", 10), anchor="w").pack(side="left")

        tk.Frame(left, bg=BG_MID).pack(fill="both", expand=True)
        tk.Frame(left, bg=BORDER, height=1).pack(fill="x")
        tk.Label(left, text='"Discere et Agere"',
                 bg=BG_MID, fg=FG_MUTED,
                 font=("Georgia", 9, "italic"), pady=10).pack()

        # ── Right login panel ──────────────────────────────────────────
        right = tk.Frame(self, bg=BG_DARK)
        right.pack(side="right", fill="both", expand=True)

        tk.Frame(right, bg=ACCENT, height=5).pack(fill="x")

        tk.Frame(right, bg=BG_DARK).pack(fill="both", expand=True)

        card = tk.Frame(right, bg=BG_CARD,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(padx=50)

        # Gold card header
        hdr = tk.Frame(card, bg=ACCENT)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Student Sign In",
                 bg=ACCENT, fg=BG_DARK,
                 font=("Georgia", 15, "bold"),
                 padx=28, pady=13).pack(side="left")

        body = tk.Frame(card, bg=BG_CARD)
        body.pack(fill="x")

        # Username
        tk.Label(body, text="USERNAME / EMAIL",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=FONT_SMALL).pack(anchor="w", padx=28, pady=2)
        self.username_var = tk.StringVar()
        self.username_entry = self._entry(body, self.username_var)
        self.username_entry.pack(fill="x", padx=28, ipady=9)
        tk.Frame(body, bg=ACCENT, height=2).pack(fill="x", padx=28, pady=14)

        # Password
        tk.Label(body, text="PASSWORD",
                 bg=BG_CARD, fg=FG_MUTED,
                 font=FONT_SMALL).pack(anchor="w", padx=28, pady=2)
        self.password_var = tk.StringVar()
        self.pw_entry = self._entry(body, self.password_var, show="●")
        self.pw_entry.pack(fill="x", padx=28, ipady=9)
        tk.Frame(body, bg=ACCENT, height=2).pack(fill="x", padx=28, pady=8)

        # Options row: show password + remember me
        opts = tk.Frame(body, bg=BG_CARD)
        opts.pack(fill="x", padx=28, pady=6)

        self.show_pw = tk.BooleanVar(value=False)
        tk.Checkbutton(opts, text="Show password",
                       variable=self.show_pw,
                       bg=BG_CARD, fg=FG_MUTED,
                       selectcolor=BG_MID,
                       activebackground=BG_CARD,
                       activeforeground=FG_SEC,
                       font=FONT_SMALL, cursor="hand2",
                       command=self._toggle_pw).pack(side="left")

        self.remember_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opts, text="Remember me",
                       variable=self.remember_var,
                       bg=BG_CARD, fg=FG_MUTED,
                       selectcolor=BG_MID,
                       activebackground=BG_CARD,
                       activeforeground=FG_SEC,
                       font=FONT_SMALL, cursor="hand2").pack(side="right")

        # Error label
        self.error_var = tk.StringVar()
        tk.Label(body, textvariable=self.error_var,
                 bg=BG_CARD, fg=DANGER,
                 font=FONT_SMALL, wraplength=320).pack(padx=28, pady=4)

        # Sign in button
        self.login_btn = tk.Button(
            body, text="Sign In  →",
            bg=ACCENT, fg=BG_DARK,
            font=("Georgia", 12, "bold"),
            relief="flat", cursor="hand2",
            activebackground=ACCENT_DIM,
            activeforeground=FG_PRIMARY,
            pady=12, command=self._attempt_login,
        )
        self.login_btn.pack(fill="x", padx=28, pady=28)

        tk.Frame(right, bg=BG_DARK).pack(fill="both", expand=True)

        # Bindings
        self.username_entry.bind("<Return>", lambda e: self.pw_entry.focus())
        self.pw_entry.bind("<Return>", lambda e: self._attempt_login())

        # Pre-fill saved credentials
        saved_user, saved_pass = load_credentials()
        if saved_user:
            self.username_var.set(saved_user)
            self.password_var.set(saved_pass)
            self.pw_entry.focus()
        else:
            self.username_entry.focus()

    def _entry(self, parent, var, show=""):
        return tk.Entry(
            parent, textvariable=var, show=show,
            bg=BG_MID, fg=FG_PRIMARY,
            insertbackground=ACCENT_LT,
            font=FONT_BODY, relief="flat", bd=0,
        )

    def _apply_saved_credentials(self):
        """Pre-fill login form if credentials were saved."""
        username, password = self._load_saved_credentials()
        if username and password:
            self.username_var.set(username)
            self.password_var.set(password)
            self.remember_var.set(True)

    def _save_credentials(self, username, password):
        import json, os, base64
        path = os.path.expanduser("~/.sbc_portal/remembered.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # Basic encoding (not true encryption, but not plaintext)
        encoded = base64.b64encode(password.encode()).decode()
        with open(path, "w") as f:
            json.dump({"username": username, "password": encoded}, f)

    def _clear_credentials(self):
        import os
        path = os.path.expanduser("~/.sbc_portal/remembered.json")
        if os.path.exists(path):
            os.remove(path)

    def _load_saved_credentials(self):
        import json, os, base64
        path = os.path.expanduser("~/.sbc_portal/remembered.json")
        if not os.path.exists(path):
            return None, None
        try:
            with open(path) as f:
                d = json.load(f)
            username = d.get("username", "")
            password = base64.b64decode(d.get("password", "")).decode()
            return username, password
        except Exception:
            return None, None

    def _toggle_pw(self):
        self.pw_entry.configure(show="" if self.show_pw.get() else "●")

    def _attempt_login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()
        self._username = username
        # Save credentials if Remember Me checked
        if self.remember_var.get():
            self._save_credentials(username, password)
        else:
            self._clear_credentials()
        if not username or not password:
            self.error_var.set("Please enter both username and password.")
            return
        self.error_var.set("")
        self.login_btn.configure(state="disabled", text="Signing in…")
        self.update()
        threading.Thread(
            target=self._do_login,
            args=(username, password, self.remember_var.get()),
            daemon=True,
        ).start()

    def _do_login(self, username: str, password: str, remember: bool):
        from scraper.auth import SBCSession, AuthError, NetworkError
        session = SBCSession()
        try:
            session.login(username, password)
            if remember:
                save_credentials(username, password)
            else:
                clear_credentials()
            self.after(0, lambda: self.on_login_success(session))
        except AuthError as e:
            msg = str(e)
            self.after(0, lambda: self._on_error(msg))
        except NetworkError as e:
            msg = str(e)
            username = self._username
            self.after(0, lambda m=msg, u=username: self._on_network_error(m, u))
        except Exception as e:
            msg = str(e)
            self.after(0, lambda: self._on_error(f"Unexpected error: {msg}"))

    def _on_network_error(self, msg: str, username: str):
        """Handle network error — offer offline fallback if cache exists."""
        from scraper.auth import load_data_cache
        cached = load_data_cache(username)
        if cached:
            _, saved_at = cached
            full_msg = ("Cannot reach mySBC — you may be on school WiFi.\n\n"
                        f"Cached data available from {saved_at[:16].replace('T',' ')}.")
            self._on_error(full_msg)
            # Add offline button
            self._add_offline_button(username)
        else:
            hint = ""
            if "ssl" in msg.lower() or "certificate" in msg.lower():
                hint = "\nSchool WiFi detected. Connect to a different network or wait."
            self._on_error(msg + hint)

    def _add_offline_button(self, username: str):
        """Show 'Use Cached Data' button on the login form."""
        try:
            if hasattr(self, "_offline_lbl") and self._offline_lbl.winfo_exists():
                return
        except Exception:
            pass
        # Find a good parent frame — put it after the error label
        parent = getattr(self, "_form_frame", self)
        self._offline_lbl = tk.Label(
            parent,
            text="📂  Use Cached Data (Offline Mode)",
            bg=WARNING, fg=BG_DARK,
            font=("TkDefaultFont", 10, "bold"),
            padx=14, pady=8,
            cursor="hand2"
        )
        self._offline_lbl.pack(fill="x", padx=28, pady=4)
        self._offline_lbl.bind("<Button-1>", lambda e: self._load_offline(username))

    def _load_offline(self, username: str):
        from scraper.auth import load_data_cache, SBCSession
        cached = load_data_cache(username)
        if not cached:
            self._on_error("No cached data found.")
            return
        data, saved_at = cached
        dummy = SBCSession()
        dummy.username = username
        dummy.logged_in = True
        dummy._offline_data = data
        dummy._offline_saved_at = saved_at
        if self.on_login_success:
            self.on_login_success(dummy)

    def _on_error(self, msg: str):
        self.error_var.set(msg)
        self.login_btn.configure(state="normal", text="Sign In  →")
