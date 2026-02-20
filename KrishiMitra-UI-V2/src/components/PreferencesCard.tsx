import { useEffect, useMemo, useState } from "react";
import { useApp } from "../lib/store";
import { market, farms } from "../lib/api";
import MultiSelect from "./MultiSelect";

export default function PreferencesCard() {
  const { state, dispatch } = useApp();
  const farm = state.farm;
  const farmId = farm?.id || "";
  const farmDistrict = farm?.district || "";

  // Metadata
  const [allCommodities, setAllCommodities] = useState<string[]>([]);
  const [allDistricts, setAllDistricts] = useState<string[]>([]);
  const [mandiOptions, setMandiOptions] = useState<string[]>([]);

  // Form state
  const [district, setDistrict] = useState<string>(farmDistrict);
  const [selected, setSelected] = useState<string[]>(farm?.preferred_commodities || []);
  const [mandi, setMandi] = useState<string>(farm?.preferred_mandi || "");

  const [loadingMeta, setLoadingMeta] = useState(true);
  const [loadingMandis, setLoadingMandis] = useState(false);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  // ----- Load encoder-backed metadata -----
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setLoadingMeta(true);
        const meta = await market.metaAll();
        if (!alive) return;
        setAllCommodities(meta.commodities || []);
        setAllDistricts(meta.districts || []);
      } catch (e: any) {
        if (alive) setErr(e?.message || "Failed to load metadata");
      } finally {
        if (alive) setLoadingMeta(false);
      }
    })();
    return () => { alive = false; };
  }, []);

  // ----- Load mandis for chosen district -----
  useEffect(() => {
    let alive = true;
    // Clear when empty
    if (!district) {
      setMandiOptions([]);
      setMandi("");
      return;
    }
    (async () => {
      try {
        setLoadingMandis(true);
        const m = await market.mandis(district);
        if (!alive) return;
        setMandiOptions(m.mandis || []);
        // If previously selected mandi is not in new list, clear it
        if (m.mandis && !m.mandis.includes(mandi)) setMandi("");
      } catch (e: any) {
        if (alive) setErr(e?.message || "Failed to load mandis");
      } finally {
        if (alive) setLoadingMandis(false);
      }
    })();
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [district]);

  // ----- Save prefs + district into farm (personalization everywhere) -----
  async function save() {
    if (!farmId) {
      setErr("Please create a farm profile first.");
      return;
    }
    setSaving(true);
    setErr(null);
    setOk(null);
    try {
      // 1) save preferences (commodities + optional mandi)
      await farms.setPrefs(farmId, {
        preferred_commodities: selected,
        preferred_mandi: mandi || null,
      });

      // 2) If user changed district via this card, patch it into farm so it’s used globally
      if (district && district !== farmDistrict) {
        dispatch({ type: "UPDATE_FARM_PARTIAL", patch: { district } });
      }

      // 3) Update local store prefs (so Market/Forecast/Ask AI pick them up)
      dispatch({
        type: "UPDATE_FARM_PARTIAL",
        patch: { preferred_commodities: [...selected], preferred_mandi: mandi || null },
      });

      setOk("Preferences saved.");
    } catch (e: any) {
      setErr(e?.message || "Failed to save preferences");
    } finally {
      setSaving(false);
      setTimeout(() => { setOk(null); setErr(null); }, 2000);
    }
  }

  // Filtered districts for quick typeahead
  const filteredDistricts = useMemo(() => {
    const q = (district || "").toLowerCase();
    if (!q) return allDistricts.slice(0, 50);
    return allDistricts.filter(d => d.toLowerCase().includes(q)).slice(0, 50);
  }, [district, allDistricts]);

  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-gray-200">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Market Preferences</h2>
      </div>

      {err && !err.toLowerCase().includes("failed to fetch") && (
        <div className="mb-3 rounded-md border border-red-200 bg-red-50 p-2 text-sm text-red-700">{err}</div>
      )}
      {ok && <div className="mb-3 rounded-md border border-green-200 bg-green-50 p-2 text-sm text-green-700">{ok}</div>}

      <div className="space-y-5">
        {/* District combo (searchable; allows free-text if not found) */}
        <div>
          <label className="mb-2 block text-sm font-medium text-gray-700">District</label>
          <input
            list="km-districts"
            className="input"
            value={district}
            onChange={(e) => setDistrict(e.target.value)}
            placeholder="Start typing to search…"
          />
          <datalist id="km-districts">
            {filteredDistricts.map((d) => <option key={d} value={d} />)}
            <option value="Other…" /> {/* user can type anything if not listed */}
          </datalist>
          <div className="mt-1 text-xs text-gray-500">
            Type to search. If your district isn’t listed, you can enter it as free text.
          </div>
        </div>

        {/* Default mandi (depends on district) */}
        <div>
          <label className="mb-2 block text-sm font-medium text-gray-700">Default mandi (optional)</label>
          <select
            className="input"
            disabled={!district || loadingMandis}
            value={mandi}
            onChange={(e) => setMandi(e.target.value)}
          >
            <option value="">{district ? "— None —" : "Set district first"}</option>
            {mandiOptions.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
          <div className="mt-1 text-xs text-gray-500">
            Used across Prices, Forecast and Ask AI unless a page overrides it.
          </div>
        </div>

        {/* Commodities multiselect */}
        <div>
          <label className="mb-2 block text-sm font-medium text-gray-700">
            Crops you sell (select multiple)
          </label>
          {loadingMeta ? (
            <div className="text-sm text-gray-500">Loading options…</div>
          ) : (
            <MultiSelect options={allCommodities} value={selected} onChange={setSelected} max={20} />
          )}
          <div className="mt-1 text-xs text-gray-500">
            Selected: {selected.length}
            {selected.length ? ` – ${selected.slice(0, 5).join(", ")}${selected.length > 5 ? "…" : ""}` : ""}
          </div>
        </div>

        <div className="flex gap-2">
          <button className="btn-primary" onClick={save} disabled={saving || (!district && !selected.length)}>
            {saving ? "Saving…" : "Save Preferences"}
          </button>
          <button
            className="btn-secondary"
            onClick={() => {
              setDistrict(farmDistrict);
              setSelected(farm?.preferred_commodities || []);
              setMandi(farm?.preferred_mandi || "");
              setErr(null);
              setOk(null);
            }}
            disabled={saving}
          >
            Reset
          </button>
        </div>
      </div>
    </section>
  );
}
