import streamlit as st

# ----------------------------
# Convert input time to microseconds
# ----------------------------
def to_microseconds(value, unit):
    if unit == "ns":
        return value / 1000
    if unit == "us":
        return value
    if unit == "ms":
        return value * 1000
    if unit == "s":
        return value * 1_000_000
    raise ValueError("Unit must be 'ns', 'us', 'ms', 's'")


# ----------------------------
# Convert back from microseconds
# ----------------------------
def from_microseconds(value_us, unit):
    if unit == "ns":
        return value_us * 1000
    if unit == "us":
        return value_us
    if unit == "ms":
        return value_us / 1000
    if unit == "s":
        return value_us / 1_000_000


# ----------------------------
# Compute WDT intervals
# ----------------------------
def compute_wdt_intervals(desired_us, tolerance=1.0):
    results = []

    # WDT dividers (2^6, 2^9, ..., 2^31)
    wdt_dividers = {f"2^{i}": 2**i for i in [6,9,13,15,19,23,27,31]}

    # 1️⃣ First try ACLK (32768 Hz)
    ACLK = 32768
    for wdt_name, wdt_div in wdt_dividers.items():
        t_us = (wdt_div / ACLK) * 1_000_000
        error = abs(t_us - desired_us)
        results.append({
            "Source": "ACLK",
            "Frequency": ACLK,
            "Divider": wdt_name,
            "time_us": t_us,
            "error_us": error
        })

    # Check if ACLK gives acceptable result
    best_aclk = min(results, key=lambda x: x["error_us"])
    if best_aclk["error_us"] <= tolerance:
        return results, best_aclk

    # 2️⃣ If not, continue with DCO / MCLK / SMCLK
    dco_freqs = [1_000_000, 2_000_000, 4_000_000, 8_000_000,
                 12_000_000, 16_000_000, 20_000_000, 24_000_000]

    # MCLK/SMCLK prescalers
    cs_dividers = {
        "DIV1": 1,
        "DIV2": 2,
        "DIV4": 4,
        "DIV8": 8
    }

    # Mapping for register names
    divm_codes = {
        1: "DIVM_0",
        2: "DIVM_1",
        4: "DIVM_2",
        8: "DIVM_3",
        16: "DIVM_4"
    }
    divs_codes = {
        1: "DIVS_0",
        2: "DIVS_1",
        4: "DIVS_2",
        8: "DIVS_3",
        16: "DIVS_4"
    }

    for dco in dco_freqs:
        for divm_name, divm in cs_dividers.items():  # MCLK divider
            mclk = dco / divm
            for divs_name, divs in cs_dividers.items():  # SMCLK divider
                smclk = mclk / divs
                for wdt_name, wdt_div in wdt_dividers.items():
                    t_us = (wdt_div / smclk) * 1_000_000
                    error = abs(t_us - desired_us)
                    results.append({
                        "Source": "SMCLK",
                        "DCO": dco,
                        "MCLK_DIV": divm,
                        "MCLK_DIV_CODE": divm_codes[divm],
                        "MCLK": mclk,
                        "SMCLK_DIV": divs,
                        "SMCLK_DIV_CODE": divs_codes[divs],
                        "SMCLK": smclk,
                        "WDT_DIV": wdt_name,
                        "time_us": t_us,
                        "error_us": error
                    })

    best = min(results, key=lambda x: x["error_us"])
    return results, best


# ----------------------------
# STREAMLIT UI
# ----------------------------
st.title("⏱ MSP430 Watchdog Timer Interval Calculator (ACLK first, then DCO/SMCLK/MCLK)")
st.write("Mai întâi verifică ACLK fix la 32768 Hz, apoi trece la DCO/SMCLK/MCLK dacă nu găsește potrivire exactă. WDT folosește divizori 2^6 … 2^31.")

# User input
value = st.number_input("Timp dorit:", min_value=0.0, step=0.1)
unit = st.selectbox("Unitate de timp:", ["ns", "us", "ms", "s"])

if st.button("Calculează"):
    desired_us = to_microseconds(value, unit)
    results, best = compute_wdt_intervals(desired_us)

    st.subheader("Rezultate calculate")
    st.dataframe([
        {
            "Source": r.get("Source", ""),
            "DCO (Hz)": r.get("DCO", ""),
            "MCLK_DIV": r.get("MCLK_DIV_CODE", r.get("MCLK_DIV", "")),
            "MCLK (Hz)": r.get("MCLK", ""),
            "SMCLK_DIV": r.get("SMCLK_DIV_CODE", r.get("SMCLK_DIV", "")),
            "SMCLK (Hz)": r.get("SMCLK", ""),
            "Frequency (Hz)": r.get("Frequency", ""),
            "WDT_DIV": r.get("Divider", r.get("WDT_DIV", "")),
            "Time (us)": round(r["time_us"], 3),
            "Error (us)": round(r["error_us"], 3)
        }
        for r in results
    ])

    best_time_converted = from_microseconds(best['time_us'], unit)
    best_error_converted = from_microseconds(best['error_us'], unit)

st.subheader("Recomandare optimă")
if best["Source"] == "ACLK":
    st.success(
        f"Source: ACLK\n"
        f"Frequency: {best['Frequency']} Hz\n"
        f"WDT_DIV: {best['Divider']}\n"
        f"Timp generat: {best_time_converted:.6f} {unit}\n"
        f"Eroare: {best_error_converted:.6f} {unit}"
    )
else:
    st.success(
        f"Source: SMCLK\n"
        f"DCO: {best['DCO']} Hz\n"
        f"MCLK_DIV: {best['MCLK_DIV_CODE']} → MCLK = {best['MCLK']} Hz\n"
        f"SMCLK_DIV: {best['SMCLK_DIV_CODE']} → SMCLK = {best['SMCLK']} Hz\n"
        f"WDT_DIV: {best['WDT_DIV']}\n"
        f"Timp generat: {best_time_converted:.6f} {unit}\n"
        f"Eroare: {best_error_converted:.6f} {unit}"
    )

