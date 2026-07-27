const BASE_URL = "http://localhost:8000"
export default function CatalogGrid({ items, selectedId, onSelect }) {
  console.log(items)
  if (!items.length) {
    return <p className="hint">loading catalogue...</p> }
return (
    <div className="catalog-grid">
      {items.map((item) => (
        <button
          key={item.id}
          className={`catalog-card ${selectedId === item.id ? "selected" : ""}`}
          onClick={() => onSelect(item)}>
          <img
            src={`${BASE_URL}/${item.image}`}
            alt={item.name}
            className="catalog-image"
        onError={(e) => { e.target.style.display = "none" }}/>
          <div className="catalog-info">
            <p className="catalog-name">{item.name}</p>
            <p className="catalog-meta">{item.material} · {item.type}</p>
          </div>
        </button>))}
    </div>)}