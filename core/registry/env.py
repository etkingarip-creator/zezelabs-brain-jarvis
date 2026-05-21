ENV_SCHEMA = {
    "DEEPSEEK_API_KEY": {"required": False, "secret": True},
    "DEEPSEEK_MODEL": {"default": "deepseek-chat"},
    "RABBITMQ_HOST": {"default": "localhost"},
    "RABBITMQ_PORT": {"default": 5672},
    "RABBITMQ_USER": {"default": "guest"},
    "RABBITMQ_PASS": {"default": "guest"},
}

def load_env():
    import os
    res = {}
    for k, v in ENV_SCHEMA.items():
        val = os.getenv(k)
        if val is None:
            res[k] = v.get("default", "")
        else:
            default_val = v.get("default")
            if default_val is not None:
                if isinstance(default_val, bool):
                    res[k] = val.lower() in ("true", "1", "yes")
                else:
                    try:
                        res[k] = type(default_val)(val)
                    except ValueError:
                        res[k] = val
            else:
                res[k] = val
    return res
