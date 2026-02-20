import { useState, useRef } from "react";
import { disease, type DiseaseDetectResult } from "../lib/api";

export default function DiseasePage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [res, setRes] = useState<DiseaseDetectResult | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  function onPick(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0] || null;
    setFile(f);
    setRes(null);
    setErr(null);
    if (f) {
      const url = URL.createObjectURL(f);
      setPreview(url);
    } else {
      setPreview(null);
    }
  }

  async function onDetect() {
    if (!file) return;
    setLoading(true);
    setErr(null);
    setRes(null);
    try {
      const out = await disease.detect(file);
      if (!out.success) {
        throw new Error(out.error || "Detection failed");
      }
      setRes(out);
    } catch (e: any) {
      setErr(e?.message || "Detection failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl p-4 space-y-4">
      <h1 className="text-xl font-semibold">Crop Disease Detection</h1>

      <section className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-gray-200">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="text-sm text-gray-700">
            Upload a clear photo of an affected leaf. JPG/PNG works best.
          </div>
          <div className="flex gap-2">
            <button
              className="btn-secondary"
              onClick={() => inputRef.current?.click()}
            >
              Choose Photo
            </button>
            <input
              ref={inputRef}
              type="file"
              accept="image/*"
              capture="environment"
              className="hidden"
              onChange={onPick}
            />
            <button
              className="btn-primary"
              onClick={onDetect}
              disabled={!file || loading}
            >
              {loading ? "Analyzing…" : "Detect Disease"}
            </button>
          </div>
        </div>

        {preview && (
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <div>
              <div className="mb-2 text-sm font-semibold">Preview</div>
              <img
                src={preview}
                alt="preview"
                className="max-h-72 w-full rounded-xl object-contain ring-1 ring-gray-200"
              />
            </div>
            <div>
              <div className="mb-2 text-sm font-semibold">Result</div>
              {err && <div className="text-sm text-red-600">{err}</div>}
              {!err && !res && <div className="text-sm text-gray-500">No result yet.</div>}
              {res && (
                <div className="space-y-3 text-sm">
                  <div>
                    <div className="font-medium">Top Prediction</div>
                    {res.diseases?.[0] ? (
                      <div>
                        {res.diseases[0]}{" "}
                        {typeof res.disease_probabilities?.[0] === "number" &&
                          `— ${(res.disease_probabilities[0] * 100).toFixed(0)}%`}
                      </div>
                    ) : (
                      <div className="text-gray-500">—</div>
                    )}
                  </div>

                  {res.diseases && res.diseases.length > 1 && (
                    <div>
                      <div className="font-medium">Other possibilities</div>
                      <ul className="list-disc pl-5">
                        {res.diseases.slice(1).map((d, i) => (
                          <li key={i}>
                            {d}
                            {typeof res.disease_probabilities?.[i + 1] === "number" &&
                              ` — ${(res.disease_probabilities![i + 1] * 100).toFixed(0)}%`}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {res.symptoms?.length ? (
                    <div>
                      <div className="font-medium">Symptoms</div>
                      <ul className="list-disc pl-5">
                        {res.symptoms.map((s, i) => <li key={i}>{s}</li>)}
                      </ul>
                    </div>
                  ) : null}

                  {res.Treatments?.length ? (
                    <div>
                      <div className="font-medium">Treatments</div>
                      <ul className="list-disc pl-5">
                        {res.Treatments.map((t, i) => <li key={i}>{t}</li>)}
                      </ul>
                    </div>
                  ) : null}

                  {res.prevention_tips?.length ? (
                    <div>
                      <div className="font-medium">Prevention</div>
                      <ul className="list-disc pl-5">
                        {res.prevention_tips.map((p, i) => <li key={i}>{p}</li>)}
                      </ul>
                    </div>
                  ) : null}
                </div>
              )}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
