import { useEffect, useMemo, useState } from 'react'
import { Card, CardHeader, CardTitle, CardSub } from '@/components/ui'
import type { ReconField, ReconMap, ReconPreview } from '@/types'
import { FIELD_LABELS } from './reconShared'

export interface FilePreviewTab {
  key: string
  label: string
  preview: ReconPreview
  mapping?: ReconMap
}

export default function FilePreviewPanel({
  tabs,
  subtitle = 'Check the detected columns and sample values before continuing.',
}: {
  tabs: FilePreviewTab[]
  subtitle?: string
}) {
  const [activeKey, setActiveKey] = useState(tabs[0]?.key ?? '')

  useEffect(() => {
    if (!tabs.some((tab) => tab.key === activeKey)) setActiveKey(tabs[0]?.key ?? '')
  }, [activeKey, tabs])

  const active = tabs.find((tab) => tab.key === activeKey) ?? tabs[0]
  const mappedLabels = useMemo(() => {
    const labels = new Map<string, string[]>()
    for (const [field, header] of Object.entries(active?.mapping ?? {})) {
      if (!header) continue
      const current = labels.get(header) ?? []
      current.push(FIELD_LABELS[field as ReconField] ?? field)
      labels.set(header, current)
    }
    return labels
  }, [active])

  if (!active) return null
  const { preview, label } = active

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>File preview</CardTitle>
          <CardSub>{subtitle}</CardSub>
        </div>
        <div className="text-[10px] text-[var(--ink-4)] font-mono text-right">
          {preview.sample_rows.length} of {preview.row_count} rows
          {preview.omitted_count > 0 && <div>{preview.omitted_count} structural row(s) omitted</div>}
        </div>
      </CardHeader>

      <div className="px-5 pt-3 border-b border-[var(--border)]" role="tablist" aria-label="Source file preview">
        <div className="flex gap-1 overflow-x-auto">
          {tabs.map((tab) => {
            const selected = active.key === tab.key
            return (
              <button
                key={tab.key}
                type="button"
                role="tab"
                id={`file-preview-tab-${tab.key}`}
                aria-selected={selected}
                aria-controls="file-preview-panel"
                title={tab.preview.file_name}
                onClick={() => setActiveKey(tab.key)}
                className={`max-w-[260px] shrink-0 px-3 py-2 text-xs font-semibold border-b-2 transition-colors truncate ${
                  selected
                    ? 'border-[var(--accent)] text-[var(--ink)]'
                    : 'border-transparent text-[var(--ink-3)] hover:text-[var(--ink)]'
                }`}
              >
                {tab.label} <span className="font-normal text-[var(--ink-4)]">· {tab.preview.file_name}</span>
              </button>
            )
          })}
        </div>
      </div>

      <div
        id="file-preview-panel"
        role="tabpanel"
        aria-labelledby={`file-preview-tab-${active.key}`}
        className="overflow-auto max-h-[380px]"
      >
        <table className="min-w-full text-xs border-collapse">
          <thead className="sticky top-0 z-10 bg-[var(--surface-2)]">
            <tr>
              <th className="px-3 py-2 text-right font-semibold text-[var(--ink-3)] border-b border-r border-[var(--border)]">#</th>
              {preview.headers.map((header, index) => {
                const assigned = mappedLabels.get(header)
                return (
                  <th key={`${header}-${index}`} className="min-w-[130px] px-3 py-2 text-left align-bottom border-b border-r border-[var(--border)] last:border-r-0">
                    <div className="font-semibold text-[var(--ink)] whitespace-pre-line">{header}</div>
                    {assigned && (
                      <div className="mt-1 text-[10px] font-medium text-[var(--forest-2)]">
                        {assigned.join(' · ')}
                      </div>
                    )}
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody>
            {preview.sample_rows.map((row, rowIndex) => (
              <tr key={rowIndex} className="odd:bg-[var(--surface)] even:bg-[var(--canvas)]">
                <td className="px-3 py-2 text-right font-mono text-[var(--ink-4)] border-b border-r border-[var(--border)]">
                  {preview.sample_row_numbers[rowIndex] ?? rowIndex + 1}
                </td>
                {preview.headers.map((_, columnIndex) => (
                  <td key={columnIndex} className="px-3 py-2 whitespace-nowrap text-[var(--ink-2)] border-b border-r border-[var(--border)] last:border-r-0">
                    {previewCell(row[columnIndex])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {preview.sample_rows.length === 0 && (
          <div className="px-5 py-8 text-center text-xs text-[var(--ink-4)]">No sample rows were detected in this file.</div>
        )}
      </div>

      <div className="px-5 py-2.5 border-t border-[var(--border)] text-[10px] text-[var(--ink-4)]">
        <div>
          {label} · {preview.sheet_name ? `Sheet: ${preview.sheet_name} · ` : ''}
          Header row(s): {preview.header_row}{preview.header_end_row !== preview.header_row ? `–${preview.header_end_row}` : ''}
        </div>
        {preview.omitted_rows.length > 0 && (
          <div className="mt-1">
            Omitted: {preview.omitted_rows.map((row) => `row ${row.row_no} (${row.reason.replace(/_/g, ' ')})`).join(' · ')}
          </div>
        )}
      </div>
    </Card>
  )
}

function previewCell(value: string | number | boolean | null | undefined): string {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (typeof value === 'number') return value.toLocaleString('en-IN', { maximumFractionDigits: 4 })
  return value
}
