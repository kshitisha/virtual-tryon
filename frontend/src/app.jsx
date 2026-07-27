import { useState, useEffect } from "react"
import { fetchCatalog, submitTryon } from "./api"
import PhotoUpload from "./components/PhotoUpload"
import CatalogGrid from "./components/CatalogGrid"
import ResultPanel from "./components/ResultPanel"
import "./App.css"
export default function App() {
  const [catalog, setCatalog] = useState([])
  const [selectedItem, setSelectedItem] = useState(null)
  const [facePhoto, setFacePhoto] = useState(null)   
  const [handPhoto, setHandPhoto] = useState(null)  
  const [result, setResult] = useState(null)         
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
useEffect(() => {
    fetchCatalog()
      .then(setCatalog)
      .catch(() => setError("Failed to load jewellery catalogue. Is the backend running?"))
  }, [])//decides which photo does this jewellery type actually need?
  const needsHandPhoto = selectedItem && ["ring", "bracelet"].includes(selectedItem.type)
  const needsFacePhoto = selectedItem && ["necklace", "earring"].includes(selectedItem.type)
function canSubmit() {
    if (!selectedItem) return false
    if (needsHandPhoto && !handPhoto) return false
    if (needsFacePhoto && !facePhoto) return false
    return true}
async function handleTryon() {
    if (!canSubmit()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await submitTryon({
        itemId: selectedItem.id,
        facePhoto,
        handPhoto,})
      setResult(data)
    } catch (err) {
      setError(err.message || "Something went wrong. Check the backend logs.")
    } finally {
      setLoading(false)}}
//clears the result when user picks a different item,
  function handleSelectItem(item) {
    setSelectedItem(item)
    setResult(null)
    setError(null)}
return (
    <div className="app">
      <header className="app-header">
        <h1>Virtual Jewellery Try-On</h1>
        <p>Select a piece, upload your photo, and see how it looks on you.</p>
      </header>
      <main className="app-main">
        {/*1st setep pick a jewellery item */}
        <section className="section">
          <h2>1. Choose a piece</h2>
          <CatalogGrid
            items={catalog}
            selectedId={selectedItem?.id}
            onSelect={handleSelectItem}/>
        </section>

        {/*second step upload the right photo based on selected item */}
        <section className="section">
          <h2>2. Upload your photo</h2>

          {!selectedItem && (
            <p className="hint">Select a jewellery item first to see which photo is needed.</p>
          )}
          {needsFacePhoto && (
            <PhotoUpload
              label="Face / upper body photo"
              hint="Used for necklaces and earrings"
              value={facePhoto}
              onChange={setFacePhoto}/>
          )}
          {needsHandPhoto && (
            <PhotoUpload
              label="Hand photo"
              hint="Used for rings and bracelets — lay your hand flat, good lighting"
              value={handPhoto}
              onChange={setHandPhoto}
            />
          )}
        </section>
{/*step 3 trigger generation */}
        <section className="section">
          <button
            className="tryon-button"
            onClick={handleTryon}
            disabled={!canSubmit() || loading}
          >
            {loading ? "Generating..." : "Try On"}
          </button>

          {/*this one shows which photo is missing without being annoying about it */}
          {selectedItem && !canSubmit() && !loading && (
            <p className="hint">
              {needsHandPhoto && !handPhoto && "Upload a hand photo to continue."}
              {needsFacePhoto && !facePhoto && "Upload a face photo to continue."}
            </p>)}
        </section>
{/* loading state */}
        {loading && (
          <div className="loading">
            <div className="spinner" />
            <p>Generating your try-on image — this takes about 15–20 seconds.</p>
          </div>)}
{/* error state */}
        {error && (
          <div className="error-banner">
            <strong>Error:</strong> {error}
          </div>)}{/* result */}
        {result && !loading && (
          <section className="section">
            <h2>Result</h2>
            <ResultPanel result={result} itemName={selectedItem?.name} />
          </section>
        )}
      </main>
    </div>
  )
}