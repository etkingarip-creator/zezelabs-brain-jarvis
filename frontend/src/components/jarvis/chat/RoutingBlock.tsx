import { getDeptStyle } from './chatHelpers';

/** ROUTING INDICATOR BLOCK */
export default function RoutingBlock({ deptId }: { deptId?: string; time?: string }) {
  const dept = getDeptStyle(deptId);
  return (
    <div
      className="flex items-center gap-2 animate-fade-in py-2 justify-center"
      style={{ marginBottom: '12px' }}
    >
      <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--content-tertiary)', fontFamily: 'var(--font-mono)', letterSpacing: '0.06em' }}>
        {deptId
          ? <><span style={{ color: dept.color }}>{dept.label.toUpperCase()}</span> departmanına yönlendiriliyor...</>
          : 'Bilişsel yönlendirme…'}
      </span>
    </div>
  );
}
