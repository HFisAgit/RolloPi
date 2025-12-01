
import pjsua as pj
import sys


# config SpeedPort Smart 3
#Du kannst dich als zusätzliche VoIP-Nebenstelle registrieren, wenn der Speedport das erlaubt (SIP-Zugangsdaten für „Internetrufnummer“ oder „IP-Telefon“).

#Im Router-Menü unter Telefonie → IP-Telefon hinzufügen (falls verfügbar).
#Dort erhältst du SIP-Zugangsdaten (Benutzername, Passwort, Registrar).



# Callback-Klasse für eingehende Anrufe
class MyCallCallback(pj.CallCallback):
    def __init__(self, call=None):
        pj.CallCallback.__init__(self, call)

    def on_state(self):
        print("Call state:", self.call.info().state_text)
        if self.call.info().state_text == "INCOMING":
            print("📞 Eingehender Anruf von:", self.call.info().remote_uri)

# Callback für eingehende SIP-Nachrichten
class MyAccountCallback(pj.AccountCallback):
    def __init__(self, account=None):
        pj.AccountCallback.__init__(self, account)

    def on_incoming_call(self, call):
        print("📞 Anruf erkannt!")
        call_cb = MyCallCallback(call)
        call.set_callback(call_cb)
        # Wir nehmen den Anruf nicht an, nur erkennen
        # call.answer(180)  # Optional: Klingelton-Signal senden

# SIP-Client starten
lib = pj.Lib()
try:
    lib.init(log_cfg=pj.LogConfig(level=3))
    lib.create_transport(pj.TransportType.UDP)
    lib.start()

    # SIP-Konto konfigurieren
    acc_cfg = pj.AccountConfig()
    acc_cfg.id = "sip:BENUTZERNAME@tel.t-online.de"
    acc_cfg.reg_uri = "sip:tel.t-online.de"
    acc_cfg.auth_cred = [pj.AuthCred("*", "PASSWORT")]

    acc = lib.create_account(acc_cfg)
    acc_cb = MyAccountCallback(acc)
    acc.set_callback(acc_cb)

    print("SIP-Client läuft. Warte auf Anrufe...")
    # Endlosschleife
    input("Drücke Enter zum Beenden...\n")

finally:
    lib.destroy()
    lib = None
