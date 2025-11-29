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

    # 1️⃣ First try ACLK (fixed 32768 Hz) with standard WDT dividers
    ACLK = 32768
    aclk_wdt_dividers = {
        "2^6": 2**6,
        "2^8": 2**8,
        "2^10": 2**10,
        "2^12": 2**12
    }

    for wdt_name, wdt_div in aclk_wdt_dividers.items():
        t_us = (wdt_div / ACLK) * 1_000_000
        error = abs(t_us - desired_us)
        results.append({
            "Source": "ACLK",
            "Frequency": ACLK,
            "Divider": wdt_name,
            "time_us": t_us,
            "error_us": error
        })

    # If exact match within tolerance found, no need for DCO calculations
    best_aclk = min(results, key=lambda x: x["error_us"])
    if best_aclk["error_us"] <= tolerance:
        return results, best_aclk

    # 2️⃣ If not, continue with DCO / MCLK / SMCLK
    # DCO frequencies (max 24 MHz)
    dco_freqs = [1_000_000, 2_000_000, 4_000_000, 8_000_000,
                 12_000_000, 16_000_000, 20_000_000, 24_000_000]
    cs_dividers = {"DIV1": 1, "DIV2": 2, "DIV4": 4, "DIV8": 8}
    wdt_dividers = {
        "2^6": 2**6,
        "2^9": 2**9,
        "2^13": 2**13,
        "2^15": 2**15,
        "2^19": 2**19,
        "2^23": 2**23,
        "2^27": 2**27,
        "2^31": 2**31
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
                        "MCLK_DIV": divm_name,
                        "MCLK": mclk,
                        "SMCLK_DIV": divs_name,
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
st.title("⏱ MSP430 Watchdog Timer Interval Calculator (ACLK first, then DCO)")
st.write("Mai întâi verifică ACLK fix la 32768 Hz, apoi trece la DCO/SMCLK/MCLK dacă nu găsește potrivire exactă.")

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
            "MCLK_DIV": r.get("MCLK_DIV", ""),
            "MCLK (Hz)": r.get("MCLK", ""),
            "SMCLK_DIV": r.get("SMCLK_DIV", ""),
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
            f"WDT_DIV: {best['Divider']}\n\n"
            f"Timp generat: **{best_time_converted:.6f} {unit}**\n"
            f"Eroare: **{best_error_converted:.6f} {unit}**"
        )
    else:
        st.success(
            f"Source: SMCLK\n"
            f"DCO: {best['DCO']} Hz\n"
            f"MCLK_DIV: {best['MCLK_DIV']} → MCLK = {best['MCLK']} Hz\n"
            f"SMCLK_DIV: {best['SMCLK_DIV']} → SMCLK = {best['SMCLK']} Hz\n"
            f"WDT_DIV: {best['WDT_DIV']}\n\n"
            f"Timp generat: **{best_time_converted:.6f} {unit}**\n"
            f"Eroare: **{best_error_converted:.6f} {unit}**"
        )



