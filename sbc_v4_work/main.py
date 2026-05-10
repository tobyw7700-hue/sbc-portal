"""
SBC Academic Portal - Main Entry Point
"""
import tkinter as tk

CURRENT_VERSION = "4.2"
GITHUB_RELEASE_API = "https://api.github.com/repos/tobyw7700-hue/sbc-portal/releases/latest"


def _check_for_update(root):
    """Check GitHub for a newer release in the background. Shows a prompt if found."""
    import threading

    def fetch():
        try:
            import urllib.request, json
            req = urllib.request.Request(
                GITHUB_RELEASE_API,
                headers={"User-Agent": "sbc-portal-updater"}
            )
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read())
            tag = data.get("tag_name", "").lstrip("v")
            url = data.get("html_url", "https://github.com/tobyw7700-hue/sbc-portal/releases/latest")
            if tag and tag != CURRENT_VERSION:
                root.after(0, lambda: _prompt_update(root, tag, url))
        except Exception:
            pass  # Silently ignore — no internet, rate limited, etc.

    threading.Thread(target=fetch, daemon=True).start()


def _prompt_update(root, new_version, url):
    """Show a non-blocking update banner at the top of the window."""
    import webbrowser
    banner = tk.Frame(root, bg="#1e3a1e", cursor="hand2")
    banner.place(x=0, y=0, relwidth=1)

    msg = tk.Label(
        banner,
        text=f"⬆️  Update available — v{new_version} is out!  Click here to download.",
        bg="#1e3a1e", fg="#86efac",
        font=("TkDefaultFont", 10, "bold"),
        pady=6, padx=16
    )
    msg.pack(side="left")

    close_btn = tk.Label(banner, text="  ✕  ", bg="#1e3a1e", fg="#86efac",
                          font=("TkDefaultFont", 12), cursor="hand2")
    close_btn.pack(side="right", padx=8)
    close_btn.bind("<Button-1>", lambda e: banner.destroy())

    def open_release(e=None):
        webbrowser.open(url)

    banner.bind("<Button-1>", open_release)
    msg.bind("<Button-1>", open_release)
    banner.bind("<Enter>", lambda e: banner.configure(bg="#14532d"))
    banner.bind("<Leave>", lambda e: banner.configure(bg="#1e3a1e"))
    msg.bind("<Enter>", lambda e: banner.configure(bg="#14532d"))
    msg.bind("<Leave>", lambda e: banner.configure(bg="#1e3a1e"))

    # Push app content down so banner doesn't overlap
    root.after(100, lambda: banner.lift())


def main():
    root = tk.Tk()
    root.title("SBC Academic Portal")
    root.geometry("1100x720")
    root.minsize(900, 600)

    from ui.app import SBCApp
    app = SBCApp(root)

    # Check for updates after a short delay so the UI loads first
    root.after(2000, lambda: _check_for_update(root))

    root.mainloop()


if __name__ == "__main__":
    main()
