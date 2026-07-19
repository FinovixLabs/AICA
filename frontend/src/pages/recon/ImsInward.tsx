import ReconWorkspace from './ReconWorkspace'

// IMS Inward: the recipient acts on inward invoices, reconciled against their
// own Purchase Register. Two-file flow, with IMS Status carried per transaction.
export default function ImsInward() {
  return (
    <ReconWorkspace
      module="ims_inward"
      title="IMS Inward Management"
      subtitle="Match on Supplier GSTIN, document type and document number; invoice-value differences are flagged for action."
      cpLabel="IMS Inward"
      showIms={true}
    />
  )
}
