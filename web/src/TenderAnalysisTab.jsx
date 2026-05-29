import { useState } from 'react'
import { AnalysisDecisionBrief } from './TenderAnalysisDecisionBrief'
import { AnalysisEvidencePanel } from './TenderAnalysisEvidencePanel'
import {
  AnalysisSectionBody,
  AnalysisSectionRail,
  analysisSectionItems,
} from './TenderAnalysisSections'
import { AnalysisSummary } from './TenderAnalysisSummary'

export function TenderAnalysisTab({ analysis, analyzing, onAnalyze, reportHref, documents = [] }) {
  const [selectedAnalysisSection, setSelectedAnalysisSection] = useState('blockers')
  const analysisSections = analysisSectionItems(analysis, documents)

  return (
    <section className="detail-section active analysis-section">
      <div className="section-heading-row analysis-action-row">
        <div>
          <h3>Анализ ТЗ</h3>
          <p className="muted-text">Риски, требования и доказательства из документов.</p>
        </div>
        <div className="analysis-actions">
          <button className="secondary-button compact" disabled={analyzing} onClick={onAnalyze} type="button">
            {analyzing ? 'Анализ...' : 'Проанализировать'}
          </button>
          <a className="secondary-link-button compact" href={reportHref}>
            Скачать Word
          </a>
        </div>
      </div>

      <AnalysisSummary analysis={analysis} documents={documents} />
      <AnalysisDecisionBrief
        analysis={analysis}
        documents={documents}
        onOpenSection={setSelectedAnalysisSection}
      />

      <div className="analysis-workspace">
        <AnalysisSectionRail
          sections={analysisSections}
          selectedSection={selectedAnalysisSection}
          onSelectSection={setSelectedAnalysisSection}
        />

        <div className="analysis-main-panel">
          {analysis ? (
            <AnalysisSectionBody
              sectionId={selectedAnalysisSection}
              analysis={analysis}
              documents={documents}
            />
          ) : (
            <p className="muted-text">Сначала извлеки текст документов, затем запусти анализ ТЗ.</p>
          )}
        </div>

        <AnalysisEvidencePanel documents={documents} analysis={analysis} />
      </div>
    </section>
  )
}
