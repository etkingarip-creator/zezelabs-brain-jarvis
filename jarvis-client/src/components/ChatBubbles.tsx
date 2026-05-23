import { motion, AnimatePresence } from 'framer-motion';

export interface Message {
  id: string;
  sender: 'user' | 'jarvis' | 'system';
  text: string;
}

interface ChatBubblesProps {
  messages: Message[];
}

export default function ChatBubbles({ messages }: ChatBubblesProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', padding: '10px 0', overflowY: 'auto', flex: 1, maxHeight: '420px' }}>
      <AnimatePresence initial={false}>
        {messages.map((msg) => (
          <motion.div
            key={msg.id}
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, transition: { duration: 0.15 } }}
            transition={{ type: 'spring', stiffness: 260, damping: 25 }}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignSelf: msg.sender === 'user' ? 'flex-end' : msg.sender === 'jarvis' ? 'flex-start' : 'center',
              maxWidth: '80%',
            }}
          >
            {/* Header / Avatar block */}
            <span style={{
              fontSize: '10px',
              fontWeight: 'bold',
              marginBottom: '4px',
              fontFamily: 'Segoe UI',
              alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
              color: msg.sender === 'user' ? '#64748b' : msg.sender === 'jarvis' ? '#00f2fe' : '#ff007f'
            }}>
              {msg.sender === 'user' ? '👤 KULLANICI ⚡' : msg.sender === 'jarvis' ? '⚡ JARVIS' : '⚠️ SİSTEM'}
            </span>

            {/* Bubble contents */}
            <div style={{
              padding: '12px 16px',
              borderRadius: '12px',
              fontFamily: 'Segoe UI',
              fontSize: '14px',
              lineHeight: '1.4',
              color: '#ffffff',
              background: msg.sender === 'user' ? 'linear-gradient(135deg, #ff007f, #7928ca)' : msg.sender === 'jarvis' ? '#0d1527' : '#070d19',
              border: msg.sender === 'user' ? 'none' : msg.sender === 'jarvis' ? '1px solid #1c2842' : '1px solid #ff007f',
              boxShadow: msg.sender === 'user' ? '0 4px 15px rgba(255, 0, 127, 0.25)' : 'none'
            }}>
              {msg.text}
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
