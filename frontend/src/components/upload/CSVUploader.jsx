import React, { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

export default function CSVUploader({ onFile, loading }) {
  const [fileName, setFileName] = useState(null);

  const onDrop = useCallback((accepted) => {
    if (accepted[0]) {
      setFileName(accepted[0].name);
      onFile(accepted[0]);
    }
  }, [onFile]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "text/csv": [".csv"] },
    multiple: false,
    disabled: loading,
  });

  return (
    <div {...getRootProps()} className={`dropzone${isDragActive ? " active" : ""}`}>
      <input {...getInputProps()} id="csv-upload-input" />
      <div className="dropzone-icon">{loading ? "⏳" : fileName ? "✅" : "📂"}</div>
      {loading ? (
        <div className="dropzone-title">Processing upload…</div>
      ) : fileName ? (
        <>
          <div className="dropzone-title">{fileName}</div>
          <div className="dropzone-sub">Click or drag to replace</div>
        </>
      ) : (
        <>
          <div className="dropzone-title">
            {isDragActive ? "Drop the CSV here" : "Drag & drop your CSV file"}
          </div>
          <div className="dropzone-sub">
            or click to browse — supports student-mat.csv / student-por.csv format
          </div>
        </>
      )}
    </div>
  );
}
