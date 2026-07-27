const BASE_URL = "http://localhost:8000"
export default function ResultPanel({ result, itemName }) {
  const { image_url, video_url } = result
  return (
    <div className="result-panel">
      <div className="result-image-wrap">
        <img
          src={`${BASE_URL}${image_url}`}
          alt={`Try-on result for ${itemName}`}
          className="result-image"/>
        <a
          href={`${BASE_URL}${image_url}`}
          download
          className="download-link">
          Download image
        </a>
      </div>
      {video_url ? (
        <div className="result-video-wrap">
          <p className="result-label">Generated video</p>
          <video
            src={`${BASE_URL}${video_url}`}
            controls
            autoPlay
            loop
            muted
            className="result-video"/>
        </div>
      ) : (
        <p className="hint">
          Video generation was skipped or is not configured.
          The try-on image above is your result.
        </p>
      )}
    </div>)}