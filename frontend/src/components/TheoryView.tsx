import type { TheoryContent } from "../types";

interface Props {
  content: TheoryContent;
}

export function TheoryView({ content }: Props) {
  return (
    <div className="space-y-8 max-w-2xl">
      {/* Explanation */}
      <section>
        <p className="text-sm text-[#111] leading-relaxed">{content.explanation}</p>
      </section>

      {/* Key points */}
      {content.key_points.length > 0 && (
        <section>
          <h3 className="text-xs font-semibold text-[#555] uppercase tracking-wide mb-3">
            Key Points
          </h3>
          <ul className="space-y-2 border-l-2 border-[#E4E4E4] pl-4">
            {content.key_points.map((point, i) => (
              <li key={i} className="text-sm text-[#111] leading-relaxed">
                {point}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Definitions */}
      {content.definitions.length > 0 && (
        <section>
          <h3 className="text-xs font-semibold text-[#555] uppercase tracking-wide mb-3">
            Definitions
          </h3>
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-[#E4E4E4]">
                <th className="text-left py-2 pr-4 text-xs font-semibold text-[#555] w-1/3">Term</th>
                <th className="text-left py-2 text-xs font-semibold text-[#555]">Definition</th>
              </tr>
            </thead>
            <tbody>
              {content.definitions.map((def, i) => (
                <tr key={i} className="border-b border-[#F0F0F0]">
                  <td className="py-2 pr-4 text-xs font-medium text-[#111] align-top">{def.term}</td>
                  <td className="py-2 text-xs text-[#333] leading-relaxed align-top">{def.definition}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}
