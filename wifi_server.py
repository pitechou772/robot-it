import network
import socket
import ubinascii
import machine

WIFI_MDP  = "robot1234"
MAX_LOGS  = 500   # nb max de lignes gardees en memoire
_INSTANCE = None


def get_instance():
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = WifiServer()
    return _INSTANCE


def log(msg):
    """Remplace print() : affiche ET stocke dans le buffer de logs."""
    print(msg)
    get_instance()._stocker(msg)


class WifiServer:

    def __init__(self):
        self._logs   = []   # lignes courantes (max MAX_LOGS)
        self._total  = 0    # compteur absolu croissant (ne diminue jamais)
        self._actif  = False
        self._ssid   = None
        self._ap     = None
        self._srv    = None

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def demarrer(self):
        if self._actif:
            log("[WiFi] Deja actif : {}".format(self._ssid))
            return

        uid        = ubinascii.hexlify(machine.unique_id()).decode()
        self._ssid = "Robot-" + uid[-4:].upper()

        self._ap = network.WLAN(network.AP_IF)
        self._ap.config(ssid=self._ssid, password=WIFI_MDP, security=4)
        self._ap.active(True)

        self._srv = socket.socket()
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        self._srv.bind(addr)
        self._srv.listen(3)
        self._srv.setblocking(False)

        self._actif = True
        log("[WiFi] AP : {}  |  MDP : {}  |  IP : {}".format(
            self._ssid, WIFI_MDP, self._ap.ifconfig()[0]))
        log("[WiFi] Ouvre http://192.168.4.1 pour voir les logs")

    def arreter(self):
        if not self._actif:
            return
        try:
            self._srv.close()
        except Exception:
            pass
        try:
            self._ap.active(False)
        except Exception:
            pass
        self._srv   = None
        self._ap    = None
        self._actif = False
        log("[WiFi] Point d'acces arrete")

    def tick(self):
        """Appele dans la boucle principale — retourne immediatement si rien a faire."""
        if not self._actif:
            return
        try:
            conn, _ = self._srv.accept()
        except OSError:
            return  # pas de connexion en attente, on rend la main tout de suite

        try:
            # Lecture non-bloquante de la requete (timeout tres court)
            conn.settimeout(0.05)
            requete = b""
            try:
                requete = conn.recv(256)
            except OSError:
                pass

            chemin = self._extraire_chemin(requete)

            if chemin.startswith("/logs"):
                reponse = self._reponse_logs(chemin)
            else:
                reponse = self._reponse_page()

            # Envoi avec timeout court pour ne pas bloquer
            conn.settimeout(0.5)
            conn.sendall(reponse)
        except Exception as e:
            print("[WiFi] Erreur:", e)
        finally:
            conn.close()

    @property
    def actif(self):
        return self._actif

    # ------------------------------------------------------------------
    # Interne
    # ------------------------------------------------------------------

    def _stocker(self, msg):
        self._logs.append(str(msg))
        self._total += 1
        if len(self._logs) > MAX_LOGS:
            self._logs.pop(0)

    @property
    def _offset(self):
        """Index absolu de self._logs[0]."""
        return self._total - len(self._logs)

    def _extraire_chemin(self, requete):
        try:
            ligne = requete.split(b"\r\n")[0].decode('utf-8', 'ignore')
            return ligne.split(" ")[1] if " " in ligne else "/"
        except Exception:
            return "/"

    def _reponse_logs(self, chemin):
        """Retourne uniquement les nouvelles lignes (format texte brut)."""
        depuis = 0
        if "depuis=" in chemin:
            try:
                depuis = int(chemin.split("depuis=")[1].split("&")[0])
            except Exception:
                pass

        rel     = max(0, depuis - self._offset)
        lignes  = self._logs[rel:]
        corps   = "\n".join(lignes)
        entetes = (
            "HTTP/1.0 200 OK\r\n"
            "Content-Type: text/plain; charset=utf-8\r\n"
            "X-Total: {}\r\n"          # index absolu apres ces lignes
            "Connection: close\r\n\r\n"
        ).format(self._total)
        return (entetes + corps).encode('utf-8')

    def _reponse_page(self):
        """Page HTML statique — envoyee une seule fois, le JS gere le reste."""
        html = (
            "<!DOCTYPE html><html><head>"
            "<meta charset='utf-8'>"
            "<title>Robot Logs</title>"
            "<style>"
            "body{margin:0;font-family:monospace;font-size:13px;"
            "background:#0d1117;color:#c9d1d9;}"
            "header{position:sticky;top:0;background:#161b22;"
            "padding:10px 16px;border-bottom:1px solid #30363d;"
            "display:flex;align-items:center;gap:12px;}"
            "h1{margin:0;color:#58a6ff;font-size:16px;flex:1;}"
            "#etat{font-size:11px;color:#8b949e;}"
            "#logs{padding:8px 16px;}"
            ".ligne{padding:3px 6px;border-radius:3px;}"
            ".ligne:nth-child(odd){background:#161b22;}"
            "</style></head><body>"
            "<header>"
            "<h1>Robot Logs</h1>"
            "<span id='etat'>connexion...</span>"
            "</header>"
            "<div id='logs'></div>"
            "<script>"
            "var depuis=0,div=document.getElementById('logs'),et=document.getElementById('etat');"
            "function poll(){"
            "  fetch('/logs?depuis='+depuis)"
            "  .then(function(r){"
            "    var t=parseInt(r.headers.get('X-Total')||depuis);"
            "    r.text().then(function(txt){"
            "      if(txt.trim()){"
            "        txt.split('\\n').forEach(function(l){"
            "          if(!l)return;"
            "          var d=document.createElement('div');"
            "          d.className='ligne';"
            "          d.textContent=l;"
            "          div.appendChild(d);"
            "        });"
            "        window.scrollTo(0,document.body.scrollHeight);"
            "      }"
            "      depuis=t;"
            "      et.textContent=depuis+' lignes | '+new Date().toLocaleTimeString();"
            "    });"
            "  })"
            "  .catch(function(){et.textContent='hors ligne';});"
            "}"
            "poll();setInterval(poll,3000);"
            "</script>"
            "</body></html>"
        )
        entetes = (
            "HTTP/1.0 200 OK\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            "Connection: close\r\n\r\n"
        )
        return (entetes + html).encode('utf-8')
