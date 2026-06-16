import React, { useCallback, useState } from "react";
import { CheckCircle2, FileUp, Loader2 } from "lucide-react";
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

  const Icon = loading ? Loader2 : fileName ? CheckCircle2 : FileUp;

  return (
    <div {...getRootProps()} className={`dropzone${isDragActive ? " active" : ""}${loading ? " loading" : ""}`}>
      <input {...getInputProps()} id="csv-upload-input" />
      <div className="dropzone-icon"><Icon size={44} className={loading ? "spin-icon" : ""} /></div>
      {loading ? (
        <>
          <div className="dropzone-title">Processing upload</div>
          <div className="dropzone-sub">Predictions and interventions are being generated.</div>
        </>
      ) : fileName ? (
        <>
          <div className="dropzone-title">{fileName}</div>
          <div className="dropzone-sub">Click or drag a new file to replace it.</div>
        </>
      ) : (
        <>
          <div className="dropzone-title">
            {isDragActive ? "Drop the CSV here" : "Drag and drop your CSV file"}
          </div>
          <div className="dropzone-sub">
            Or click to browse. Supports standard comma or semicolon-delimited student CSV files.
          </div>
        </>
      )}
    </div>
  );
}
