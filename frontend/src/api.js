import axios from "axios"
const BASE_URL = "http://localhost:8000"
export async function fetchCatalog() {
  const res = await axios.get(`${BASE_URL}/catalog`)
  return res.data}
export async function submitTryon({ itemId, facePhoto, handPhoto }) {
  //multipart/form-data axios handles this automatically when given FormData
  const form = new FormData()
  form.append("item_id", itemId)
if (facePhoto) form.append("face_photo", facePhoto)
if (handPhoto) form.append("hand_photo", handPhoto)
try {
    const res = await axios.post(`${BASE_URL}/tryon`, form, {
      //generous timeout
      timeout: 120_000,})
    return res.data
  } catch (err) {
    //pull the actual error message out of FastAPI's response body if available
    const detail = err.response?.data?.detail
    throw new Error(detail || "Request failed — check the backend is running")
  }
}