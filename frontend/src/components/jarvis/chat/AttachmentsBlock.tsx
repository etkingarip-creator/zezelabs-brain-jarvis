import { FileText } from 'lucide-react';
import type { ChatAttachment } from '../../../types/department';

/** ATTACHMENTS VIEW BLOCK */
export default function AttachmentsBlock({ attachments }: { attachments?: ChatAttachment[] }) {
  if (!attachments || attachments.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-2.5 mt-2.5">
      {attachments.map((file, idx) => {
        const isImage = file.type.startsWith('image/');
        const isAudio = file.type.startsWith('audio/');
        const isVideo = file.type.startsWith('video/');
        const sizeKB = (file.size / 1024).toFixed(1);

        return (
          <div
            key={idx}
            className="flex flex-col border rounded-xl overflow-hidden bg-slate-900/40 relative max-w-sm"
            style={{ borderColor: 'rgba(255, 255, 255, 0.06)' }}
          >
            {isImage && (
              <img src={file.url} alt={file.name} className="max-h-48 object-contain bg-black/20" />
            )}
            {isVideo && (
              <video src={file.url} controls className="max-h-48 object-contain bg-black/20" />
            )}
            {isAudio && (
              <div className="p-3">
                <audio src={file.url} controls className="w-full max-w-xs" />
              </div>
            )}
            {!isImage && !isVideo && !isAudio && (
              <div className="flex items-center gap-2.5 p-3">
                <FileText className="w-8 h-8 p-1.5 rounded bg-slate-800 text-cyan-400" />
                <div className="min-w-0 flex-1">
                  <span className="block text-xs text-slate-200 truncate font-medium">{file.name}</span>
                  <span className="block text-[10px] text-slate-500 font-mono">{sizeKB} KB</span>
                </div>
              </div>
            )}

            {(isImage || isVideo) && (
              <div className="p-2 bg-slate-950/40 border-t border-white/5 flex items-center justify-between text-[10px] text-slate-400 font-mono">
                <span className="truncate max-w-[150px]">{file.name}</span>
                <span>{sizeKB} KB</span>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
