import { useState } from "react";
import type { PracticalContent } from "../types";

interface Props {
  content: PracticalContent;
}

export function PracticalView({ content }: Props) {
  const [openExamples, setOpenExamples] = useState<Set<number>>(new Set());

  function toggle(i: number) {
    setOpenExamples((prev) => {
      const next = new Set(prev);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });
  }

  return (
    <div className="space-y-8 max-w-2xl">
      {/* Overview */}
      <section>
        <p className="text-sm text-[#111] leading-relaxed">{content.overview}</p>
      </section>

      {/* Examples accordion */}
      {content.examples.length > 0 && (
        <section>
          <h3 className="text-xs font-semibold text-[#555] uppercase tracking-wide mb-3">
            Examples
          </h3>
          <div className="border border-[#E4E4E4] rounded divide-y divide-[#E4E4E4]">
            {content.examples.map((ex, i) => {
              const isOpen = openExamples.has(i);
              return (
                <div key={i}>
                  <button
                    onClick={() => toggle(i)}
                    className="w-full flex items-center justify-between px-4 py-3 text-sm text-[#111] font-medium text-left hover:bg-[#F4F4F4] transition-colors"
                  >
                    <span>{ex.title}</span>
                    <span className="ml-2 shrink-0 text-[#aaa] font-normal">{isOpen ? "−" : "+"}</span>
                  </button>
                  {isOpen && (
                    <div className="px-4 pb-4 space-y-3">
                      {ex.description && (
                        <p className="text-sm text-[#333] leading-relaxed">{ex.description}</p>
                      )}
                      {ex.steps.length > 0 && (
                        <ol className="space-y-1.5 list-decimal list-inside">
                          {ex.steps.map((step, si) => (
                            <li key={si} className="text-sm text-[#333] leading-relaxed">
                              {step}
                            </li>
                          ))}
                        </ol>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Tips */}
      {content.tips.length > 0 && (
        <section>
          <h3 className="text-xs font-semibold text-[#555] uppercase tracking-wide mb-3">Tips</h3>
          <ul className="space-y-2 border-l-2 border-[#E4E4E4] pl-4">
            {content.tips.map((tip, i) => (
              <li key={i} className="text-sm text-[#111] leading-relaxed">
                {tip}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
