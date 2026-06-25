import type { ChatAttachment } from '../../../types/department';
import AttachmentsBlock from './AttachmentsBlock';

/** USER INPUT BLOCK */
export default function InputBlock({ text, attachments }: { text: string; time?: string; attachments?: ChatAttachment[] }) {
  return (
    <div
      className="self-end max-w-[80%] animate-fade-in-up"
      style={{
        background: 'rgba(255, 255, 255, 0.05)',
        border: '1px solid rgba(255, 255, 255, 0.04)',
        borderRadius: '16px',
        padding: '10px 14px',
        marginBottom: '12px',
        marginLeft: 'auto',
      }}
    >
      <p style={{ fontSize: 'var(--text-sm)', color: 'var(--content-primary)', lineHeight: 1.5 }}>
        {text}
      </p>
      <AttachmentsBlock attachments={attachments} />
    </div>
  );
}
