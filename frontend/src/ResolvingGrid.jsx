import "./ResolvingGrid.css";

const MESSY_ROWS = [
  ["ord-1", "john doe", "104.5"],
  ["ord-2", "  JANE  ", ""],
  ["ord-2", "  JANE  ", ""],
  ["", "bob", "88"],
  ["ord-4", "Alice!!", "2201"],
];

const CLEAN_ROWS = [
  ["ORD-1", "John Doe", "104.50"],
  ["ORD-2", "Jane", "0.00"],
  ["ORD-3", "Bob", "88.00"],
  ["ORD-4", "Alice", "2201.00"],
];

function GridBlock({ rows, variant }) {
  return (
    <div className={`rg-grid rg-grid--${variant}`}>
      {rows.map((row, i) => (
        <div className="rg-row" key={i}>
          {row.map((cell, j) => (
            <span className="rg-cell" key={j}>
              {cell === "" ? <span className="rg-null">null</span> : cell}
            </span>
          ))}
        </div>
      ))}
    </div>
  );
}

export default function ResolvingGrid() {
  return (
    <div className="rg-wrap" role="img" aria-label="A messy spreadsheet resolving into a clean, normalized one">
      <GridBlock rows={MESSY_ROWS} variant="messy" />
      <div className="rg-scan" />
      <GridBlock rows={CLEAN_ROWS} variant="clean" />
    </div>
  );
}
