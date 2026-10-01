interface StatusBadgeProps {
  status: "online" | "offline" | "degraded" | "maintenance";
  className?: string;
}

export default function StatusBadge({ status, className }: StatusBadgeProps) {
  const statusStyles: Record<string, string> = {
    online: "bg-green-100 text-green-800 border-green-300",
    offline: "bg-red-100 text-red-800 border-red-300",
    degraded: "bg-yellow-100 text-yellow-800 border-yellow-300",
    maintenance: "bg-blue-100 text-blue-800 border-blue-300",
  };

  const style = statusStyles[status] || statusStyles.offline;

  return (
    <span
      className={`px-3 py-1 rounded-full text-xs font-semibold border ${style} ${className || ""}`}
    >
      {status.toUpperCase()}
    </span>
  );
}