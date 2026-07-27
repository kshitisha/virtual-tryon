import { useRef } from "react"
export default function PhotoUpload({ label, hint, value, onChange }) {
  const inputRef = useRef(null)
  function handleFileChange(e) {
    const file = e.target.files[0]
    if (file) onChange(file)}
    function handleDrop(e) {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file && file.type.startsWith("image/")) onChange(file)
  }
function handleDragOver(e) {
    e.preventDefault()
  }//for display only
  const previewUrl = value ? URL.createObjectURL(value) : null
  return (
    <div className="photo-upload">
      <p className="upload-label">{label}</p>
      {hint && <p className="upload-hint">{hint}</p>}
      <div
        className={`upload-zone ${value ? "has-file" : ""}`}
        onClick={() => inputRef.current.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >{previewUrl ? (
          <img src={previewUrl} alt="preview" className="upload-preview" />
        ) : (
          <span className="upload-placeholder">
            Click or drag an image here
          </span> )}
      </div>
{/* hidden*/}
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        style={{ display: "none" }}
        onChange={handleFileChange}/>
{value && (
        <button
          className="remove-photo"
          onClick={(e) => {
            e.stopPropagation()
            onChange(null)
          }}>
          Remove photo
        </button>
      )}
    </div>)}