export function formatPrice(amount: number, currency: string): string {
  const major = Math.round(amount / 100);
  const formatted = major
    .toString()
    .replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  const symbol = currency === "RUB" ? "₽" : currency;
  return `${formatted} ${symbol}`;
}
