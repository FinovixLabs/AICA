import ReconWorkspace from './ReconWorkspace'

export default function Gstr2b() {
  return (
    <ReconWorkspace
      module="gstr2b"
      title="GSTR-2B Reconciliation"
      subtitle="Match the purchase register against GSTR-2B. Invoice value decides the match, within 1% tolerance."
      cpLabel="GSTR-2B"
      showIms={false}
    />
  )
}
