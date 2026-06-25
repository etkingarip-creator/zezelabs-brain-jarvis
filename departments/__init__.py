# departments package - all agents
try:
    from .app_factory.agent import AppFactoryAgent
except ImportError:
    AppFactoryAgent = None

try:
    from .crypto_trading.agent import CryptoTradingAgent
except ImportError:
    CryptoTradingAgent = None

try:
    from .media_factory.agent import MediaFactoryAgent
except ImportError:
    MediaFactoryAgent = None

try:
    from .zeze_aro.agent import ZezeAroAgent
except ImportError:
    ZezeAroAgent = None

try:
    from .zeze_design.agent import ZezeDesignAgent
except ImportError:
    ZezeDesignAgent = None

try:
    from .zeze_rnd.agent import ZezeRndAgent
except ImportError:
    ZezeRndAgent = None

try:
    from .zeze_trend.agent import ZezeTrendAgent
except ImportError:
    ZezeTrendAgent = None

try:
    from .zeze_sec.agent import ZezeSecAgent
except ImportError:
    ZezeSecAgent = None

try:
    from .zeze_business.agent import ZezeBusinessAgent
except ImportError:
    ZezeBusinessAgent = None

try:
    from .zeze_comms.agent import ZezeCommsAgent
except ImportError:
    ZezeCommsAgent = None

try:
    from .zeze_compliance.agent import ZezeComplianceAgent
except ImportError:
    ZezeComplianceAgent = None

try:
    from .zeze_dev.agent import ZezeDevAgent
except ImportError:
    ZezeDevAgent = None

try:
    from .zeze_ops.agent import ZezeOpsAgent
except ImportError:
    ZezeOpsAgent = None

try:
    from .zeze_production.agent import ZezeProductionAgent
except ImportError:
    ZezeProductionAgent = None

try:
    from .zeze_game.agent import ZezeGameAgent
except ImportError:
    ZezeGameAgent = None

__all__ = [
    'AppFactoryAgent',
    'CryptoTradingAgent',
    'MediaFactoryAgent',
    'ZezeAroAgent',
    'ZezeDesignAgent',
    'ZezeRndAgent',
    'ZezeSecAgent',
    'ZezeTrendAgent',
    'ZezeBusinessAgent',
    'ZezeCommsAgent',
    'ZezeComplianceAgent',
    'ZezeDevAgent',
    'ZezeOpsAgent',
    'ZezeProductionAgent',
    'ZezeGameAgent',
]
