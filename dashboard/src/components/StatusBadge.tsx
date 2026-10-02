interface StatusBadgeProps {
  status: "online" | "offline" | "degraded" | "maintenance";
  className?: string;
  size?: "sm" | "md" | "lg";
  showDot?: boolean;
}

export default function StatusBadge({ status, className, size = "md", showDot = true }: StatusBadgeProps) {
  const sizeStyles = {
    sm: { padding: "0.125rem 0.375rem", fontSize: "0.625rem", gap: "0.25rem" },
    md: { padding: "0.25rem 0.625rem", fontSize: "0.75rem", gap: "0.375rem" },
    lg: { padding: "0.375rem 0.875rem", fontSize: "0.875rem", gap: "0.5rem" },
  };

  const style = sizeStyles[size];

  return (
    <span
      className={`status-badge status-${status} ${className || ""}`}
      style={{
        ...style,
        display: "inline-flex",
        alignItems: "center",
      } as React.CSSProperties}
    >
      {showDot && <span className={`status-dot ${status}`} style={{ width: size === "sm" ? 5 : size === "lg" ? 10 : 8, height: size === "sm" ? 5 : size === "lg" ? 10 : 8 }} />}
      {status.toUpperCase()}
    </span>
  );
}