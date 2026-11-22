/** 1～5 顆星的評分顯示 */
export const Stars = ({ value }: { value: number | null | undefined }) => {
  const n = value == null ? 0 : Math.round(Number(value));
  return (
    <span className="fw-stars" aria-label={value == null ? 'no rating' : `${value} / 5`}>
      {'★'.repeat(n)}
      <span style={{ opacity: 0.3 }}>{'★'.repeat(5 - n)}</span>
    </span>
  );
};
