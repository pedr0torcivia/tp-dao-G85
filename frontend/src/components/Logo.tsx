export function Logo({
  symbol = false,
  className = "",
}: {
  symbol?: boolean;
  className?: string;
}) {
  const asset = symbol ? "isotipo" : "logo";
  return (
    <>
      <img
        src={`/brand/${asset}.svg`}
        alt="EntreLibros"
        className={`dark:hidden ${className}`}
      />
      <img
        src={`/brand/${asset}-dark.svg`}
        alt="EntreLibros"
        className={`hidden dark:block ${className}`}
      />
    </>
  );
}
