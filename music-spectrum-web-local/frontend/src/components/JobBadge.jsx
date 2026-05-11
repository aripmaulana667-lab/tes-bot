export default function JobBadge({ status }) {
  return <span className={`badge ${status}`}>{status}</span>;
}
