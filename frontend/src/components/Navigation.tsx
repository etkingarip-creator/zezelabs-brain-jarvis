import { motion } from 'framer-motion';
import { MessageCircle, Building2 } from 'lucide-react';

interface NavigationProps {
  activeModule: 'jarvis' | 'zezelabs';
  onModuleChange: (module: 'jarvis' | 'zezelabs') => void;
}

export default function Navigation({ activeModule, onModuleChange }: NavigationProps) {
  return (
    <div className="flex items-center gap-2 p-1 bg-slate-800/50 rounded-xl border border-cyan-500/10">
      <NavItem
        id="jarvis"
        label="JARVIS"
        icon={MessageCircle}
        isActive={activeModule === 'jarvis'}
        onClick={() => onModuleChange('jarvis')}
        color="cyan"
      />
      <NavItem
        id="zezelabs"
        label="Zezelabs"
        icon={Building2}
        isActive={activeModule === 'zezelabs'}
        onClick={() => onModuleChange('zezelabs')}
        color="violet"
      />
    </div>
  );
}

interface NavItemProps {
  id: string;
  label: string;
  icon: React.ElementType;
  isActive: boolean;
  onClick: () => void;
  color: 'cyan' | 'violet';
}

function NavItem({ id, label, icon: Icon, isActive, onClick, color }: NavItemProps) {
  const colorClasses = {
    cyan: {
      active: 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border-cyan-400/30',
      hover: 'hover:bg-slate-700/50',
      icon: 'text-cyan-400',
    },
    violet: {
      active: 'bg-gradient-to-r from-violet-500/20 to-purple-500/20 text-violet-300 border-violet-400/30',
      hover: 'hover:bg-slate-700/50',
      icon: 'text-violet-400',
    },
  };

  return (
    <motion.button
      onClick={onClick}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={`relative flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-['Rajdhani'] font-medium transition-all border border-transparent ${
        isActive ? colorClasses[color].active : `text-cyan-400/60 ${colorClasses[color].hover}`
      }`}
    >
      <Icon className={`w-4 h-4 ${isActive ? '' : colorClasses[color].icon}`} />
      {label}
      {isActive && (
        <motion.div
          layoutId="activeIndicator"
          className="absolute inset-0 rounded-lg border border-current pointer-events-none"
          transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
        />
      )}
    </motion.button>
  );
}
