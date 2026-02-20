interface StatsCardProps {
  icon: string;
  value: number;
  label: string;
  variant: "accent" | "success" | "warning" | "danger" | "info";
}

export default function StatsCard({ icon, value, label, variant }: StatsCardProps) {
  return (
    <div className={`stat-card ${variant}`}>
      <div className="stat-card-icon">{icon}</div>
      <div className="stat-card-value">{value.toLocaleString()}</div>
      <div className="stat-card-label">{label}</div>
    </div>
  );
}
