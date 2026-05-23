DEPARTMENTS = {
    "app_factory": {
        "queue": "zeze_app_factory_queue",
        "allowed_tools": ["file_read", "file_edit", "code_analysis"],
        "forbidden_tools": ["live_trade", "git_push", "withdrawal"],
    },
    "zeze_aro": {
        "queue": "zeze_aro_queue",
        "allowed_tools": ["file_read", "roi_record", "loop_record"],
        "forbidden_tools": ["live_trade", "git_push"],
    },
    "media_factory": {
        "queue": "zeze_media_queue",
        "allowed_tools": ["file_read", "file_edit", "roi_record", "loop_record"],
        "forbidden_tools": ["live_trade", "withdrawal", "git_push"],
    },
    "crypto_trading": {
        "queue": "zeze_crypto_queue",
        "allowed_tools": ["file_read", "file_edit", "shell_exec"],
        "forbidden_tools": ["live_trade", "withdrawal", "leverage"],
    },
    "zeze_sec": {
        "queue": "zeze_sec_queue",
        "allowed_tools": ["code_analyze", "vulnerability_scan", "prompt_audit", "dlp_scan"],
        "forbidden_tools": ["live_trade", "git_push_external"],
    },
    "zeze_rnd": {
        "queue": "zeze_rnd_queue",
        "allowed_tools": ["web_scan", "code_analysis", "tech_eval", "autonomous_inject"],
        "forbidden_tools": ["live_trade", "git_push_external"],
    },
    "zeze_prompt": {
        "queue": "zeze_prompt_queue",
        "allowed_tools": ["prompt_refine", "template_render", "cognitive_map", "file_read"],
        "forbidden_tools": ["live_trade", "git_push_external"],
    },
    "zeze_eng": {
        "queue": "zeze_eng_queue",
        "allowed_tools": ["file_read", "file_edit", "shell_exec", "git_commit"],
        "forbidden_tools": ["live_trade", "withdrawal"],
    },
    "zeze_guard": {
        "queue": "zeze_guard_queue",
        "allowed_tools": ["roi_record", "loop_record", "limit_check"],
        "forbidden_tools": ["live_trade", "withdrawal", "git_push"],
    },
    "zeze_design": {
        "queue": "zeze_design_queue",
        "allowed_tools": ["visual_generation", "parametric_design", "layout_composition", "n8n_integration"],
        "forbidden_tools": ["live_trade"],
    },
}

