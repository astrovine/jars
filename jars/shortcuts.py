SHORTCUTS = {
    "al": "auth login",
    "ar": "auth register",
    "alo": "auth logout",
    "ala": "auth logout-all",
    "a2s": "auth 2fa-setup",
    "a2v": "auth 2fa-verify",
    "apr": "auth password-reset",
    "who": "auth whoami",
    
    "um": "user me",
    "uf": "user full",
    "uu": "user update",
    "up": "user password",
    "ua": "user activity",
    "ued": "user ensure-demo",
    "uup": "user upgrade-plus",
    "uub": "user upgrade-business",
    
    "wb": "wallet balance",
    "ws": "wallet summary",
    "wh": "wallet history",
    "wd": "wallet deposit",
    "wvd": "wallet verify-deposit",
    "wba": "wallet banks",

    "wvs": "wallet virtual-status",
    "wvrf": "wallet virtual-reset-free",
    "wvrp": "wallet virtual-reset-paid",
    
    "tl": "traders list",
    "tp": "traders profile",
    "tm": "traders me",
    "ta": "traders apply",
    "tk": "traders kyc",
    "tks": "traders kyc-submit",
    "tu": "traders update",
    "td": "traders deactivate",
    "tr": "traders reactivate",
    
    "sl": "subs list",
    "sf": "subs follow",
    "su": "subs unfollow",
    "sp": "subs pause",
    "sr": "subs resume",
    "ss": "subs subscribers",
    "st": "subs tier",
    
    "pp": "payments pricing",
    "pu": "payments upgrade",
    "pv": "payments verify",
    "pb": "payments banks",
    
    "kl": "keys list",
    "ka": "keys add",
    "kt": "keys test",
    "kd": "keys delete",

    "?": "help",
    "h": "help",
    "q": "exit",
}

def resolve_alias(cmd_input: str) -> str:
    parts = cmd_input.strip().split()
    if not parts:
        return cmd_input
        
    cmd = parts[0].lower()
    
    if cmd in SHORTCUTS:
        replacement = SHORTCUTS[cmd]
        return replacement + " " + " ".join(parts[1:])
        
    return cmd_input
