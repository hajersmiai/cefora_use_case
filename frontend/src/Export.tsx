import ExportModal, { type ExportFormat } from "./pages/export_model";
import { useState } from "react";

export default function DemoExport() {
  const [open, setOpen] = useState(true);
  const [fmt, setFmt] = useState<ExportFormat>("csv");

  return (
    <ExportModal
      open={open}
      chosenFormat={fmt}
      onChooseFormat={setFmt}
      selectionLabel="IT Sector, Brussels Region"
      recordsLabel="2,453 job offers"
      onCancel={() => setOpen(false)}
      onClose={() => setOpen(false)}
      onDownload={() => {
        // déclenche ton export selon fmt
        console.log("download:", fmt);
      }}
    />
  );
}
