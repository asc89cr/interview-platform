<!-- Owned by Legal Advisor Agent (09). Compiled from legal research, Aug 2026. ADVISORY ONLY - not a substitute for licensed counsel. High-severity items must be reviewed by a qualified attorney before launch. -->

# Legal Risk Brief: Real-Time AI Interview Assistant Platform

**Document:** `docs/legal/legal-brief.md`
**Prepared by:** Legal Advisory
**Date:** August 13, 2026
**Version:** 1.0
**Status:** PRIVILEGED AND CONFIDENTIAL — ATTORNEY-CLIENT WORK PRODUCT

> **Scope of this brief.** This document addresses the legal and regulatory risks arising from a desktop application that (a) captures system-loopback audio (interviewer) and microphone audio (candidate) during live job interviews conducted over Zoom, Microsoft Teams, or Google Meet; (b) streams audio to the cloud for real-time transcription; (c) displays AI-generated suggested answers on a candidate-visible overlay; and (d) stores transcripts and generates coaching reports. The brief covers United States federal and state law, EU/UK data-protection law, platform terms of service, fraud and misrepresentation exposure, competitive positioning, and compliance recommendations. It is intended for internal legal review and product-risk governance. **Nothing herein is a substitute for qualified legal counsel in the applicable jurisdiction(s).**

---

## Table of Contents

1. [Recording and Wiretap Consent Laws](#1-recording-and-wiretap-consent-laws)
2. [Platform Terms of Service](#2-platform-terms-of-service)
3. [Employer/Recruiter Perspective — Fraud, Misrepresentation, and Professional Consequences](#3-employerrecruiter-perspective)
4. [The Grey-Area Framing — Competitors and Realistic Enforcement Risk](#4-the-grey-area-framing)
5. [Risk-Mitigation Recommendations](#5-risk-mitigation-recommendations)
6. [Data Privacy Compliance for Our Own Platform](#6-data-privacy-compliance-for-our-own-platform)
7. [Summary Risk Matrix](#7-summary-risk-matrix)

---

## ⚠️ Highest-Severity Risk Flags (Pre-Summary)

The following items carry the **highest legal severity** and are called out here before the detailed analysis:

| # | Risk | Severity | Why |
|---|------|----------|-----|
| R-1 | Recording interviewer audio without consent in an all-party-consent state (CA, FL, IL, PA, WA, etc.) | 🔴 CRITICAL | Criminal + civil liability; no commercial "safe harbor" |
| R-2 | Processing interviewer's voice/PII under GDPR without a lawful basis and without notice | 🔴 CRITICAL | Fines up to €20M / 4% global turnover; ICO enforcement active |
| R-3 | System-loopback audio capture in violation of Zoom/Teams/Meet AUP | 🔴 HIGH | Account termination, platform civil action, breach-of-contract exposure |
| R-4 | Deceptive use in interviews treated as fraud/misrepresentation by employers | 🔴 HIGH | Rescission of offers, civil fraud claims, industry blacklisting |
| R-5 | Storing interviewer voice/PII without DPA with sub-processors (OpenAI, Deepgram) | 🔴 HIGH | GDPR/CCPA regulatory enforcement |

---

## 1. Recording and Wiretap Consent Laws

### 1.1 United States Federal Law — The Federal Wiretap Act

The primary federal statute is **Title III of the Omnibus Crime Control and Safe Streets Act of 1968**, as amended by the **Electronic Communications Privacy Act of 1986 (ECPA)**, codified at **18 U.S.C. §§ 2510–2523**. The core prohibition is at **18 U.S.C. § 2511(1)**, which makes it a federal crime to intentionally intercept, use, or disclose wire, oral, or electronic communications.

The federal statute contains a critical exception: **18 U.S.C. § 2511(2)(d)** — the "one-party consent" rule — which permits interception where **one party to the communication has given prior consent**, *unless* the interception is for the purpose of committing a criminal or tortious act. Under the federal floor, a candidate who is a party to the conversation and who consents to recording by running the software satisfies federal law.

**However:** the federal statute expressly does **not** preempt stricter state laws. *Cf.* 18 U.S.C. § 2516. States may, and many do, require **all-party consent**.

> **Citation:** 18 U.S.C. § 2511 (Federal Wiretap Act); available at [https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title18-section2511](https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title18-section2511)

**Criminal penalties under federal law (18 U.S.C. § 2511):** Up to **5 years imprisonment** per count; civil damages of the greater of $100/day for each day of violation or $10,000 per 18 U.S.C. § 2520(c)(2).

---

### 1.2 State-Level All-Party (Two-Party) Consent Laws

> 🔴 **CRITICAL RISK AREA**

Eleven states have enacted statutes that require **all parties** to a private conversation to consent before it may be recorded. These are not technicalities — enforcement is active, civil litigation is common, and penalties are significant.

| State | Statute | Key Penalty |
|-------|---------|-------------|
| **California** | Cal. Penal Code § 632 | Criminal: misdemeanor/felony (up to $10,000 fine; up to 3 years prison). Civil: greater of **$5,000 per violation** or 3× actual damages — **no actual damages required**. |
| **Connecticut** | Conn. Gen. Stat. § 52-570d | Civil action; $10,000 minimum damages |
| **Delaware** | Del. Code tit. 11, § 1335 | Class E felony; civil damages |
| **Florida** | Fla. Stat. § 934.03 | Felony (3rd degree); civil damages including punitive |
| **Illinois** | 720 ILCS 5/14-2 (Eavesdropping Act) | Class 4 felony; civil damages including punitive |
| **Maryland** | Md. Code, Courts & Judicial Proceedings § 10-402 | Felony (up to 5 years); civil damages |
| **Massachusetts** | Mass. Gen. Laws ch. 272, § 99 | Felony (up to 5 years prison, up to $10,000 fine); civil treble damages |
| **Montana** | Mont. Code Ann. § 45-8-213 | Felony; civil damages |
| **New Hampshire** | N.H. Rev. Stat. § 570-A:2 | Class B felony; civil damages |
| **Pennsylvania** | Pa. Cons. Stat. tit. 18, § 5703 | Felony (3rd degree); civil damages |
| **Washington** | Wash. Rev. Code § 9.73.030 | Gross misdemeanor/Felony; civil: actual damages or **$1,000 per violation**, whichever is greater, plus punitive; attorney fees |

> **Citations:**
> - Cal. Penal Code § 632: [https://california.public.law/codes/penal_code_section_632](https://california.public.law/codes/penal_code_section_632)
> - Fla. Stat. § 934.03: [https://www.flsenate.gov/Laws/Statutes/2023/934.03](https://www.flsenate.gov/Laws/Statutes/2023/934.03)
> - 18 U.S.C. § 2520 (civil remedies): [https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title18-section2520](https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title18-section2520)

#### 1.2.1 Practical Implication: Interstate and Conflict-of-Laws Risk

The most common and most dangerous scenario for this product: the **interviewer is located in California, Florida, Illinois, Pennsylvania, or Washington** while the candidate is elsewhere. The candidate's one-party consent under the federal floor and their home-state law is **irrelevant**. Courts have generally applied the stricter standard when any party to a communication is in an all-party consent state. *See, e.g., Kearney v. Salomon Smith Barney, Inc.*, 39 Cal. 4th 95 (2006) (California law applied to call recorded by out-of-state party).

Because the product captures audio without the interviewer's knowledge or consent, **every interview in which the interviewer is in an all-party consent jurisdiction is a potential felony and a per-violation civil action**. The system does not know — and cannot reliably know — where the interviewer is located at the moment of the call.

#### 1.2.2 The "Loopback" Technical Argument and Its Limits

The product captures audio via **system loopback** (capturing the OS-level audio output of the interviewer's voice as transmitted over the video call). Some have argued this is not an "interception" because the audio has already been decoded and is merely being read from the audio buffer of the candidate's own device. This argument is legally untested and **should not be relied upon** as a compliance strategy because:

1. Courts have consistently read "intercept" broadly to include capturing data at any point in the transmission pathway. *See Konop v. Hawaiian Airlines, Inc.*, 302 F.3d 868 (9th Cir. 2002).
2. The substantive harm targeted by § 632 (confidential communications recorded without consent) is identical regardless of the technical method.
3. State eavesdropping statutes (notably Illinois, 720 ILCS 5/14-2) expressly cover using *any device* to hear or record a private conversation.

---

### 1.3 European Union — GDPR

> 🔴 **CRITICAL RISK AREA**

The **General Data Protection Regulation (EU) 2016/679 (GDPR)** applies when the product processes personal data of individuals located in the EU/EEA, regardless of where the company is established (GDPR Art. 3(2) — the "targeting" and "monitoring" criteria).

**The interviewer is a data subject.** Their voice, name, employer identity, and any personal statements they make during the interview constitute personal data under GDPR Art. 4(1). The product processes this data without their knowledge. This creates several simultaneous violations:

#### Lawful Basis (GDPR Art. 6)

The company must identify a valid lawful basis **before** processing. The six bases under Art. 6(1) are assessed below for the interviewer's data:

| Basis | Art. 6(1) | Assessment |
|-------|-----------|------------|
| Consent | (a) | **Unavailable.** The interviewer has not consented and is unaware of the processing. |
| Contract | (b) | **Unavailable.** No contract exists between the platform and the interviewer. |
| Legal obligation | (c) | **Unavailable.** No law requires this processing. |
| Vital interests | (d) | **Unavailable.** Does not apply. |
| Public task | (e) | **Unavailable.** Not a public authority function. |
| Legitimate interests | (f) | **Highly doubtful.** The commercial interest of helping a candidate deceive an interviewer is unlikely to survive a Legitimate Interests Assessment (LIA) balancing test. EDPB guidance requires the interest to be "genuine," "necessary," and not overridden by the data subject's interests or rights. A covert recording for competitive advantage fails this test. |

> **Without a valid Art. 6 lawful basis, every processing operation involving the interviewer's data is unlawful under GDPR.**

#### Transparency Obligations (GDPR Arts. 13–14)

Art. 14 requires that when personal data is not collected directly from the data subject, the controller must provide specified information (identity, purposes, legal basis, recipients, retention period, rights) **within a reasonable period** and at latest **within one month**. The product provides no such notice to interviewers.

#### Data Minimisation (GDPR Art. 5(1)(c))

Collecting the interviewer's full audio is not limited to what is "adequate, relevant, and limited to what is necessary." A coaching tool for candidates does not require the interviewer's voice to be stored.

#### Data Subject Rights

Interviewers have rights under Arts. 15–22 including the right to erasure (Art. 17), the right to object (Art. 21), and the right to restriction (Art. 18). The platform has no mechanism to honor these rights because the interviewer is unaware of the processing.

#### GDPR Penalties

- **Administrative fines:** Up to **€20,000,000** or **4% of total worldwide annual turnover**, whichever is higher (Art. 83(5)).
- **Supervisory authority enforcement:** National DPAs (e.g., CNIL in France, BfDI in Germany, ICO in UK) have been actively fining AI and audio-processing companies. The Irish DPC imposed a €1.2B fine on Meta in 2023.
- **Private right of action:** Art. 82 — every data subject who suffers material or non-material damage may claim compensation from the controller.

> **Citations:**
> - GDPR Art. 3 (territorial scope): [https://gdpr-info.eu/art-3-gdpr/](https://gdpr-info.eu/art-3-gdpr/)
> - GDPR Art. 6 (lawful basis): [https://gdpr-info.eu/art-6-gdpr/](https://gdpr-info.eu/art-6-gdpr/)
> - GDPR Art. 14 (data not collected from subject): [https://gdpr-info.eu/art-14-gdpr/](https://gdpr-info.eu/art-14-gdpr/)
> - GDPR Art. 83 (penalties): [https://gdpr-info.eu/art-83-gdpr/](https://gdpr-info.eu/art-83-gdpr/)

---

### 1.4 United Kingdom — UK GDPR and Data Protection Act 2018

Following Brexit, the **UK GDPR** (retained via the European Union (Withdrawal) Act 2018, supplemented by the **Data Protection Act 2018**) mirrors EU GDPR almost identically for these purposes. The **ICO** (Information Commissioner's Office) is the supervisory authority.

Key UK-specific points:
- **Regulation of Investigatory Powers Act 2000 (RIPA)** — while RIPA does not create private-sector criminal liability for one-party recording per se, **UK GDPR** independently prohibits covert processing of personal data without a lawful basis.
- **ICO Guidance on employment and monitoring** (updated 2023) makes clear that covert recording of voice data in an employment context requires an exceptional justification that "processing for interview cheating assistance" cannot meet.
- Fines: up to **£17.5 million or 4% of global annual turnover** under DPA 2018, s. 157.

> **Citation:** ICO UK GDPR guidance: [https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/)

---

## 2. Platform Terms of Service

> 🔴 **HIGH RISK AREA**

### 2.1 Zoom

The relevant Zoom governing documents are the **Zoom Terms of Service** (current version, last revised August 2023) and the **Zoom Acceptable Use Guidelines**.

**Section 4 (Acceptable Use) of the Zoom Terms of Service prohibits:**

> *"Intercepting, collecting, or storing any personally identifiable information or personal data of others from the Services or Software without their express permission."*

> *"Eavesdropping or attempting to eavesdrop on communications that you are not authorized to access."*

> *"Scraping, data mining, extracting, or harvesting any content, data, or information from the Services or Software, including by mechanical or automated means."*

> *"Accessing or using the Services or Software for purposes of monitoring availability, performance, or functionality, or for any other benchmarking or competitive purposes."*

The system-loopback capture method used by this product — capturing decoded audio output from Zoom's client running on the user's machine — does not use Zoom's API and is not authorized by Zoom. Capturing a third party's (the interviewer's) voice data from a Zoom call without their express permission directly violates the first and second prohibitions quoted above.

**Consequences:** Zoom may **terminate or suspend** the candidate's Zoom account and may bring a civil action for breach of contract. More significantly, Zoom could invoke the **Computer Fraud and Abuse Act (CFAA), 18 U.S.C. § 1030**, against the product company if the loopback mechanism is argued to "exceed authorized access" to Zoom's transmitted data streams.

> **Citation:** Zoom Terms of Service: [https://www.zoom.com/en/trust/terms/](https://www.zoom.com/en/trust/terms/); Zoom Acceptable Use Guidelines: [https://explore.zoom.us/en/trust/legal-compliance/](https://explore.zoom.us/en/trust/legal-compliance/)

---

### 2.2 Microsoft Teams

Microsoft's **Microsoft Services Agreement** and the Teams-specific **Commercial Terms** prohibit unauthorized automation and data capture.

Microsoft's Services Agreement (Section 4 — "Using the Services") states:

> *"You must not… access or use our services to harm others or to use deceptive practices… You must not… use automated means (including bots, scrapers, etc.) or other methods to access the services in ways that could harm our services or systems."*

More critically, as of **2026**, Microsoft has actively deployed technical controls to **automatically block external/unregistered AI bots** from joining Teams meetings. Any bot or process not registered within the organization's **Microsoft Entra ID (formerly Azure AD)** tenant is flagged, labeled as "external," and can be administratively blocked before it reaches the meeting lobby. This is not merely a contractual risk — it is an active technical enforcement mechanism that will prevent the product from functioning with Teams in organizationally hardened environments.

Microsoft's **compliance recording framework** (governed by the Teams Policy-Based Recording API) requires that any third-party recording or transcription solution:
1. Be a certified Microsoft compliance recording partner;
2. Operate only via the official Microsoft Graph API / Calling API;
3. Provide meeting participants with notification of recording.

A loopback-based capture tool is not compliant with this framework.

> **Citations:**
> - Microsoft Services Agreement: [https://www.microsoft.com/en-us/servicesagreement/](https://www.microsoft.com/en-us/servicesagreement/)
> - Microsoft Teams compliance recording: [https://learn.microsoft.com/en-us/microsoftteams/teams-recording-compliance](https://learn.microsoft.com/en-us/microsoftteams/teams-recording-compliance)
> - Microsoft Teams AI bot blocking (2026): [https://voip.review/2026/07/03/microsoft-teams-tightens-controls-on-ai-meeting-bots/](https://voip.review/2026/07/03/microsoft-teams-tightens-controls-on-ai-meeting-bots/)

---

### 2.3 Google Meet

Google Meet's **Acceptable Use Policy** (last updated September 11, 2025) prohibits:

> **Circumvention:** *"Do not engage in actions intended to bypass our policies or subvert restrictions placed on your account."*

> **Deceptive Practices, Fraud & Scams:** *"Do not deceive, mislead, or confuse users for financial gain or personal harm."*

> **System Interference:** *"Do not abuse this product and do not harm, degrade, or negatively affect the operation of networks, devices, or other infrastructure."*

The **Google Meet Media API**, which is the authorized pathway for third-party access to meeting audio, requires:
1. Explicit consent from participants and/or the host;
2. Visible in-meeting disclosure that audio access is active;
3. Vetting and compliance review by Google.

A loopback capture tool that bypasses the Media API and captures audio without host or participant notification violates the Circumvention and Deceptive Practices clauses above.

Google has further begun flagging third-party bots as **"Potential Risk"** participants in Meet sessions, requiring explicit host intervention to admit them. As of 2026, Google is tightening these controls in conjunction with Zoom and Microsoft in response to the Otter.ai-related congressional attention on AI bots in meetings.

> **Citations:**
> - Google Meet Acceptable Use Policy: [https://support.google.com/meet/answer/9847091?hl=en](https://support.google.com/meet/answer/9847091?hl=en)
> - Google Meet Media API controls: [https://knowledge.workspace.google.com/admin/meet/control-media-api-access-in-google-meet](https://knowledge.workspace.google.com/admin/meet/control-media-api-access-in-google-meet)

---

### 2.4 Platform Risk Summary

| Platform | ToS Clause Violated | Technical Enforcement | Account Risk |
|----------|--------------------|-----------------------|--------------|
| Zoom | §4 AUP (intercept, eavesdrop, scrape) | No API-level enforcement currently; platform can detect anomalous data flows | Account termination, civil action, potential CFAA claim |
| Microsoft Teams | MSA §4; Compliance Recording Framework | **Active bot detection + blocking as of 2026**; Entra ID gating | Account/tenant suspension; civil action |
| Google Meet | AUP (circumvention, deception, system interference) | "Potential Risk" flagging; Media API gating; admin controls | Account termination; civil action |

---

## 3. Employer/Recruiter Perspective

### 3.1 Fraud and Misrepresentation

While there is no U.S. federal statute specifically criminalizing AI interview assistance, using this product in a live interview creates **common-law fraud and misrepresentation** exposure:

**Elements of common-law fraud** (Restatement (Second) of Torts § 525):
1. A false representation of a material fact;
2. Knowledge of its falsity (scienter);
3. Intent to induce reliance;
4. Justifiable reliance by the other party;
5. Resulting damage.

The candidate using this tool represents, either explicitly or through the structure of the interview process, that their spoken answers reflect their own knowledge and judgment. The AI-generated responses that they read and parrot are a false representation of their competence. This is particularly clear in:

- **Technical/coding interviews** where the employer is explicitly evaluating the candidate's independent problem-solving ability;
- **Interviews that include a declaration** (often in the application agreement) that the candidate's representations are their own;
- **Assessments embedded in interviews** (e.g., "walk me through your thought process") where the real-time AI coaching corrupts the evidentiary value of the response.

**Promissory fraud in employment offers:** If the employer extends an offer of employment based on a fraudulently obtained positive interview result, they may have a civil fraud claim against the candidate resulting in rescission of the employment contract and/or damages. Several large tech companies' candidate agreements explicitly prohibit use of AI assistance during interviews.

### 3.2 Breach of Implied Terms and Interview Conduct Agreements

Major employers (Amazon, Meta, Google, Microsoft, Goldman Sachs, and many others) include **interview terms and conditions** in their application processes that:
- Require candidates to complete assessments without external assistance;
- Explicitly prohibit AI tools during live interviews;
- Reserve the right to rescind offers for violation of these terms.

Using this product in violation of these terms constitutes **breach of contract** (or breach of the implied contractual terms of the interview process). While specific case law on AI interview cheating is nascent, the **contractual analogy is well-established** from testing law:

### 3.3 Academic-Integrity and Proctored Testing Analogies

The closest legal analogy is proctored testing law, where there is substantial precedent:

- **ETS v. Individuals (various):** The Educational Testing Service has successfully sued for breach of contract and misrepresentation in numerous instances of testing fraud, obtaining injunctive relief and damages.
- **ProctorU and remote proctoring cases:** Courts have upheld institutions' rights to invalidate results and revoke credentials when students use unauthorized assistance. *See Ogletree v. Cleveland State University* (noting that academic dishonesty can support rescission of academic credit).
- **LSAT/Bar exam fraud:** State bar associations have permanently barred individuals discovered to have cheated on bar admission examinations, treating deception in credentialing as grounds for professional exclusion.

The same principle applies: **credentials or positions obtained through deceptive interview conduct can be rescinded**, and employers may have additional civil remedies.

### 3.4 The Cluely Precedent (Columbia University, 2025)

The most directly relevant real-world precedent is the **Columbia University disciplinary action** against the founders of Cluely (April 2025). Columbia suspended students who used their own interview-assistance AI tool to cheat during job interviews with companies including Amazon and Meta. Those companies subsequently blacklisted the candidates. This is not a court case — but it establishes the **real-world consequence pattern**: institutional disciplinary action + employer blacklisting, without any need for criminal prosecution.

> **Citation:** TechCrunch, *"Columbia student suspended over interview cheating tool raises $5.3M to cheat on everything,"* April 21, 2025: [https://techcrunch.com/2025/04/21/columbia-student-suspended-over-interview-cheating-tool-raises-5-3m-to-cheat-on-everything/](https://techcrunch.com/2025/04/21/columbia-student-suspended-over-interview-cheating-tool-raises-5-3m-to-cheat-on-everything/)

---

## 4. The Grey-Area Framing

### 4.1 How Competitors Position Themselves

The market currently includes several comparable tools. Their legal positioning varies significantly:

| Product | Legal Positioning | Disclaimers | Outcome |
|---------|-------------------|-------------|---------|
| **Final Round AI** | Primarily interview *prep* and mock interviews; copilot features available but framed as "practice" | ToS requires users to comply with all applicable laws and employer policies; liability disclaimed for consequences of live use | Lower controversy profile; raises VC and enterprise customers |
| **Cluely** (fmr. Interview Coder) | Aggressively marketed as "cheat on everything"; explicitly built for covert use | Terms shift all liability to user; company disclaims all responsibility for policy violations or legal consequences | Columbia suspension; $5.3M VC funding; massive media/legal scrutiny; 2025 data breach exposing 83,000+ users |
| **LockedIn AI** | Real-time overlay; marketed to candidates | Generic disclaimers; user assumes risk | Lower profile; less scrutiny |
| **Interview Coder** | Predecessor to Cluely; same founders | Same pattern | Rebranded after controversy |

**The key legal takeaway from competitor positioning:** Every competitor that has survived media and legal scrutiny has:
1. **Explicitly disclaimed liability** for live interview use;
2. **Shifted all legal risk** to the user through ToS;
3. **Nominally positioned** the product as "prep" or "practice" rather than "use live covertly."

However, these disclaimers have **not been tested in adversarial litigation** as of the date of this brief. They are shields against the company's direct liability — they do not protect **users** from consequences under recording law, platform ToS, or employer fraud claims.

### 4.2 Realistic Enforcement Risk — Current State (2026)

**Criminal enforcement against users:** Low probability currently. No U.S. state prosecutor has yet charged a job candidate with wiretapping for using an AI interview assistant. The political will to prosecute a job-seeker does not currently exist.

**Civil enforcement by employers against candidates:** Low-to-medium probability. Rescission of job offers has occurred (Cluely founders). Formal civil fraud lawsuits against candidates have not yet been filed publicly, likely because the discovery and proof burden is high.

**Civil enforcement by states (recording law) against the company:** Medium probability and rising. The California AG has a history of using the UCL (Cal. Bus. & Prof. Code § 17200) against tech platforms that facilitate privacy violations at scale. A mass-market deployment of this product in California creates a potential class action under § 632 with **per-violation statutory damages of $5,000 with no actual harm required**.

**Platform enforcement (Zoom/Teams/Google):** **High and rising.** Microsoft has already deployed automated bot detection and blocking. Zoom and Google have signaled (publicly, in 2026) that AI notetaker restrictions are tightening. The product may **stop working** on these platforms through technical enforcement before legal enforcement materializes.

**GDPR regulatory enforcement:** **High probability if EU users are involved.** EU DPAs have been aggressively pursuing AI audio-processing companies. The product's structure — capturing an EU-resident interviewer's voice without consent or notice — is a textbook Art. 6 + Art. 14 violation. Fines in the €100K–€10M range have been imposed for similar violations.

**Reputational enforcement:** **Already occurring at scale.** The backlash against Cluely demonstrates that reputational harm is the most immediate and tangible risk for this product category.

---

## 5. Risk-Mitigation Recommendations

> This section provides concrete, actionable steps the company should implement.

### 5.1 Product Architecture — Hardest Line

**Recommendation 5.1.A — Do Not Launch a "Live Interview" Mode Without Consent Architecture**

The highest-risk configuration of this product is silent, covert real-time operation during a live interview. Until the company has implemented the consent and technical controls described below, the product should be marketed, architected, and limited to:

1. **Practice / mock interview mode:** The product only operates when the user is in a simulated session (no real interviewer present).
2. **Post-interview coaching mode:** The product processes audio *after* the interview concludes, with the user's own audio only (no loopback of the interviewer's voice).

This positioning has meaningful legal force: it eliminates the all-party consent risk (no interviewer to consent), eliminates the GDPR third-party data-subject risk (no interviewer data), and eliminates the platform ToS interception clause risk.

**If a live mode is offered**, it should:
- Capture only the **candidate's own microphone audio** (not system loopback);
- Display a pre-session **mandatory disclosure screen** that the candidate must read and acknowledge before each session;
- Include a **geo-detection gate** (see 5.1.C below).

**Recommendation 5.1.B — Eliminate System Loopback by Default**

The system loopback capture of the interviewer's audio is the single most legally dangerous feature. Remove it from the default configuration. If loopback is offered at all, it should be:
- Explicitly opt-in;
- Accessible only after the user certifies (at the session level, not just at account creation) that all parties have consented;
- Disabled in all-party-consent jurisdictions by default (see geo-gating below).

**Recommendation 5.1.C — Implement Geo-Jurisdiction Gating**

Implement IP-based and user-declared jurisdiction gating:
1. On account creation, require users to specify their state/country.
2. Automatically disable loopback and live audio features for users whose IP or declared location is in an all-party consent state (CA, CT, DE, FL, IL, MD, MA, MT, NH, PA, WA) or EU/UK.
3. For EU/UK users, either (a) disable the product entirely for live interview use, or (b) implement a full GDPR-compliant consent flow (see §6 below).

**Note:** IP geolocation is imperfect. Geo-gating reduces but does not eliminate liability. It demonstrates good-faith effort and may be relevant to the "willfulness" element of criminal and civil statutes.

---

### 5.2 Terms of Service for Users

The company's own **Terms of Service** must include, at minimum:

1. **Explicit acknowledgment of recording laws.** A prominent clause stating that recording conversations without all-party consent may be illegal in the user's jurisdiction and that the user is solely responsible for compliance with all applicable federal, state, and local recording laws.

2. **Prohibition on illegal use.** A clause expressly prohibiting use of the product in any manner that violates applicable wiretapping, eavesdropping, or recording consent laws.

3. **Employer-policy compliance obligation.** A clause requiring users to comply with the terms and conditions of any interview, assessment, or employment process in which they participate and to ensure that use of the product is permitted by the recruiting employer.

4. **Indemnification.** A broad indemnification clause requiring the user to indemnify and hold the company harmless from any claims arising from the user's illegal or unauthorized use, including claims by third parties (interviewers, employers, platforms).

5. **Limitation of liability.** Cap the company's liability to the user at the amount paid by the user in the prior 12 months (a standard SaaS clause, but critically important here).

6. **Consequential damages waiver.** Disclaim all consequential, incidental, and punitive damages (offer rescission, blacklisting, reputational harm, etc.).

**Sample ToS Language (Jurisdiction Gate):**

```
IMPORTANT NOTICE REGARDING RECORDING LAWS. The laws of certain jurisdictions,
including but not limited to California, Florida, Illinois, Maryland,
Massachusetts, Pennsylvania, and Washington, require the consent of ALL parties
to a conversation before it may be recorded. It is your sole responsibility to
determine whether your use of the Software in a live interview complies with all
applicable laws. By enabling any audio capture feature, you represent and warrant
that you have obtained all legally required consents from all parties to the
conversation you are recording or transcribing. The Company expressly disclaims
any liability arising from your failure to obtain such consents.
```

---

### 5.3 Pre-Session Consent Gate

Implement a **per-session, click-through acknowledgment screen** that:

1. Displays the user's detected jurisdiction;
2. Displays a plain-language summary of the recording law in that jurisdiction;
3. Requires the user to affirmatively check one of two boxes:
   - "I confirm that all parties to this conversation have been informed and have consented to recording and transcription"; **or**
   - "I am using this product in Practice/Prep mode only, with no real interviewers present."
4. Logs the acknowledgment with timestamp and session ID.

This gate does not eliminate liability for illegal recording, but it:
- Documents the user's assumption of risk;
- Supports the indemnification clause;
- May be relevant to the company's good-faith defense in regulatory proceedings.

---

### 5.4 Data Handling and Retention Policy

**Default Settings:**
- **Do not store audio by default.** Audio streams should be processed in-memory and immediately discarded after transcription. Audio files should never be written to disk or stored in cloud storage unless the user explicitly opts in.
- **Transcript storage:** Transcripts may be stored, but should be retained for a maximum of **90 days** by default, with user control to extend or delete.
- **Post-interview coaching reports:** May be stored, but with the interviewer's personal data (name, employer, voice fingerprint) **redacted or not stored** (see §6.4 below).

**Right to Deletion:** Provide a self-service account deletion flow that permanently deletes all stored transcripts, reports, and audio within **30 days** of request.

---

### 5.5 Ethics Stance and Positioning

The company should adopt and publish a public-facing **Ethics and Responsible Use Policy** that:

1. **Explicitly endorses transparent use.** Position the product as "most valuable when you use it openly" — as a note-taker, a prep tool, and a coaching system — rather than as a covert assistant.
2. **Discourages covert live use.** State plainly that the company does not endorse using the product to deceive interviewers or employers and that doing so may violate law and employer policies.
3. **Distances from "cheat on everything" framing.** Given the Cluely controversy, this differentiation has both ethical and commercial value (enterprise and HR-side users will not touch a product branded as a cheating tool).
4. **Commits to no audio training data.** State that user audio is never used to train AI models and never shared with third parties beyond the named sub-processors.

---

### 5.6 Platform-Specific Risk Mitigation

- **Do not route audio through Zoom/Teams/Google APIs.** Use only OS-level audio APIs (WASAPI on Windows, Core Audio on macOS). While this does not resolve the ToS risk, it avoids triggering platform-side API monitoring.
- **Do not inject into platform processes.** Any DLL injection, process hooking, or API hooking of the video platform's own application is likely to trigger CFAA or DMCA anti-circumvention liability.
- **Monitor platform policy changes quarterly.** The ToS landscape is evolving rapidly (Microsoft's 2026 bot-blocking rollout is the clearest example). Assign responsibility for quarterly platform ToS review.

---

## 6. Data Privacy Compliance for Our Own Platform

> This section addresses the company's obligations as a **data controller** processing personal data of both candidates and interviewers.

### 6.1 Privacy Policy Requirements

The company must maintain a public-facing **Privacy Policy** that complies with:
- **GDPR Art. 13** (data collected directly from users — candidate data);
- **GDPR Art. 14** (data not collected directly — interviewer data, if processed);
- **California Consumer Privacy Act (CCPA), Cal. Civ. Code § 1798.100 et seq.**, as amended by **CPRA (Proposition 24)** and effective in final form January 1, 2023;
- Other applicable US state privacy laws (Virginia CDPA, Colorado CPA, Connecticut CTDPA, etc., effective 2023–2024).

**Minimum required disclosures in the Privacy Policy:**
1. Categories of personal data collected (audio, transcripts, name, email, employer, etc.);
2. Purposes of processing for each category;
3. Legal basis for each processing purpose (GDPR);
4. Data retention periods;
5. Categories of third parties with whom data is shared (including sub-processors by name);
6. Whether data is sold or shared for cross-context behavioral advertising (CCPA/CPRA);
7. User rights and how to exercise them;
8. Data subject contact / DPO contact information;
9. International data transfer mechanisms (e.g., EU Standard Contractual Clauses — SCCs);
10. How to submit a deletion or access request (GDPR Art. 17; CCPA § 1798.105).

> **Citation:** CCPA (OAG): [https://oag.ca.gov/privacy/ccpa](https://oag.ca.gov/privacy/ccpa); GDPR Art. 13: [https://gdpr-info.eu/art-13-gdpr/](https://gdpr-info.eu/art-13-gdpr/)

---

### 6.2 GDPR Compliance — EU/UK Users

If the product is available to users in the EU or UK (whether or not the company is established there), the following are mandatory:

**Data Controller vs. Processor:**
- The company is a **data controller** in respect of candidate data (it determines purposes and means of processing).
- The company is also a **data controller** in respect of any interviewer personal data it processes (voice, identity) — even though the interviewer has not consented to be processed.

**Data Protection Officer (DPO):**
- A DPO is required under GDPR Art. 37 if the company's "core activities consist of processing operations which, by virtue of their nature, their scope and/or their purposes, require regular and systematic monitoring of data subjects on a large scale" or if processing special category data at scale. Audio transcription at scale likely triggers this requirement. Even if technically not required, appointing a DPO is strongly recommended.

**Data Protection Impact Assessment (DPIA):**
- A DPIA (GDPR Art. 35) is **mandatory** for processing that is "likely to result in a high risk to the rights and freedoms of natural persons." Covert audio capture and AI-powered transcript generation constitute high-risk processing. The DPIA must be completed **before** the processing begins and must be updated when processing changes materially.
- The DPIA must document: description of processing; assessment of necessity and proportionality; identification of risks; and measures to address those risks.

**EU Standard Contractual Clauses (SCCs):**
- If personal data of EU data subjects is transferred to the U.S. (to company servers, or to U.S.-based sub-processors like OpenAI or Deepgram), the company must use the **2021 European Commission Standard Contractual Clauses** (Commission Implementing Decision (EU) 2021/914) as the transfer mechanism. [https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/standard-contractual-clauses-scc_en](https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/standard-contractual-clauses-scc_en)

**UK IDTA:**
- For UK-to-US transfers, the **UK International Data Transfer Agreement (IDTA)** (in force March 21, 2022) is the required mechanism. [https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/international-data-transfer-agreement-and-guidance/](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/international-data-transfer-agreement-and-guidance/)

---

### 6.3 CCPA/CPRA Compliance — US (California) Users

The **CCPA** (as amended by CPRA) grants California consumers the following rights that the platform must support:
- **Right to Know** (§ 1798.100): What categories and specific pieces of personal information are collected, used, disclosed, or sold.
- **Right to Delete** (§ 1798.105): Request deletion of personal information, subject to limited exceptions.
- **Right to Correct** (§ 1798.106, CPRA addition): Request correction of inaccurate personal information.
- **Right to Opt-Out of Sale/Sharing** (§ 1798.120): Opt out of the sale or sharing of personal information (a "Do Not Sell or Share" link is required in the Privacy Policy and footer).
- **Right to Limit Use of Sensitive Personal Information** (§ 1798.121, CPRA): Limit use of sensitive personal information (voice recordings are arguably sensitive PI under CPRA).

The platform must:
1. Post a **"Do Not Sell or Share My Personal Information"** link;
2. Respond to consumer requests within **45 calendar days** (extendable by 45 days with notice);
3. Have written contracts with all service providers that include CCPA-mandated provisions (see §6.4).

> **Citation:** California Attorney General CCPA page: [https://oag.ca.gov/privacy/ccpa](https://oag.ca.gov/privacy/ccpa); CPRA text: [https://cppa.ca.gov/regulations/](https://cppa.ca.gov/regulations/)

---

### 6.4 Sub-Processor Data Processing Agreements (DPAs)

The company shares personal data (audio, transcripts) with at minimum:
- **Deepgram** (transcription/ASR)
- **OpenAI** (AI response generation)
- Potentially: cloud infrastructure providers (AWS, GCP, Azure)

For each sub-processor, the company must:

1. **Execute a written Data Processing Agreement (DPA)** that includes:
   - Scope and purpose of processing (limited to service delivery);
   - Data subject categories and types;
   - Instructions for processing (processor may only act on documented controller instructions);
   - Security obligations (appropriate technical and organizational measures);
   - Sub-processor obligations (sub-processors must flow down equivalent obligations);
   - Assistance with data subject rights;
   - Deletion/return of data at contract end;
   - Audit rights;
   - For GDPR: Art. 28 mandatory clauses; SCCs if applicable.

2. **Maintain a written record** of all sub-processors and notify users of changes (30-day advance notice is recommended).

3. **Review and agree to:**
   - OpenAI DPA: [https://openai.com/policies/data-processing-addendum](https://openai.com/policies/data-processing-addendum) — OpenAI operates as a data processor, processes only per instructions, commits to CCPA compliance, and maintains a sub-processor list.
   - Deepgram DPA: Available at [https://deepgram.com/legal](https://deepgram.com/legal) — similar structure; restricts use to speech-to-text service delivery; requires flow-down to Deepgram's sub-processors.

4. **Confirm that sub-processors do NOT train models on your users' audio.** Both OpenAI (via the API, not the consumer product) and Deepgram offer zero-data-retention and no-training-use options. **Opt into these contractually.** This is a critical privacy and trust requirement.

---

### 6.5 Data Retention Schedule

| Data Type | Default Retention | User Control | Justification |
|-----------|------------------|--------------|---------------|
| Raw audio files | **Not stored by default**; if stored by user opt-in: 30 days | Delete on demand | Minimize legal exposure; minimize breach risk |
| Real-time transcripts (session) | 90 days | Delete on demand; export | Sufficient for coaching utility |
| Post-interview coaching reports | 12 months | Delete on demand; export | User value; reasonable commercial retention |
| Account / identity data | Duration of account + 30 days post-deletion | Account deletion flow | Legal basis: contract performance |
| AI prompt/response logs | 30 days (debugging only) | Not user-accessible | Minimize data footprint |
| Billing/payment records | 7 years | No user deletion (legal obligation) | Tax/financial compliance |

---

### 6.6 Security Requirements

- **Encryption at rest** (AES-256) for all stored transcripts and audio;
- **Encryption in transit** (TLS 1.3) for all audio streaming;
- **Access controls:** least-privilege; MFA for all staff with access to user data;
- **Incident response plan** covering GDPR Art. 33 (72-hour DPA notification) and CCPA breach notification (Cal. Civ. Code § 1798.82);
- **Penetration testing** at least annually;
- **SOC 2 Type II** certification recommended before enterprise launch.

> **Note:** The Cluely data breach (mid-2025), in which admin credentials exposed on GitHub led to the leak of personal data and interview transcripts for over **83,000 users**, is the direct cautionary precedent for this product category. Credential hygiene, secrets scanning, and security review processes are non-negotiable.

---

## 7. Summary Risk Matrix

| Risk | Probability | Severity | Primary Mitigation |
|------|-------------|----------|--------------------|
| Criminal wiretapping violation (all-party state) | Medium (rising with scale) | 🔴 Critical | Eliminate loopback; geo-gate; consent architecture |
| GDPR enforcement (interviewer data) | High if EU deployed | 🔴 Critical | Do not process interviewer audio; DPIA; DPO |
| Platform ToS violation / account ban | High (Zoom/Teams/Meet) | 🔴 High | Disclosure of method; no platform API abuse; monitor ToS |
| Civil recording law liability (CA § 632) | Medium-High | 🔴 High | Geo-gate CA; consent gate; per-violation caps via ToS |
| Employer fraud / misrepresentation claim | Medium | 🔴 High | Ethics policy; "prep not live" positioning; ToS indemnification |
| CCPA enforcement / class action | Medium | 🟠 High | Privacy policy; consumer rights flow; DPAs with sub-processors |
| Sub-processor data breach (OpenAI, Deepgram) | Low-Medium | 🟠 High | Zero-retention API options; DPAs; incident response plan |
| Federal CFAA claim (platform loopback) | Low (currently) | 🟠 High | Do not hook/intercept platform processes |
| User blacklisting / offer rescission | High (if used covertly) | 🟡 Medium | Ethics stance; disclaimer; user education |
| UK ICO enforcement | Medium if UK deployed | 🟠 High | UK IDTA; separate UK GDPR analysis |
| Reputational harm / media scrutiny | High (given sector) | 🟡 Medium | Ethics stance; responsible use policy; PR preparation |

---

## Appendix A — Key Statutes and Official Sources

| Reference | URL |
|-----------|-----|
| 18 U.S.C. § 2511 (Federal Wiretap Act) | https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title18-section2511 |
| 18 U.S.C. § 1030 (CFAA) | https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title18-section1030 |
| Cal. Penal Code § 632 | https://california.public.law/codes/penal_code_section_632 |
| Fla. Stat. § 934.03 | https://www.flsenate.gov/Laws/Statutes/2023/934.03 |
| 720 ILCS 5/14-2 (Illinois Eavesdropping) | https://www.ilga.gov/legislation/ilcs/ilcs3.asp?ActID=1876 |
| Pa. Cons. Stat. tit. 18, § 5703 | https://www.legis.state.pa.us/cfdocs/legis/LI/consCheck.cfm?txtType=HTM&ttl=18&div=0&chpt=57 |
| Wash. Rev. Code § 9.73.030 | https://app.leg.wa.gov/rcw/default.aspx?cite=9.73.030 |
| GDPR full text | https://gdpr-info.eu/ |
| GDPR Art. 6 (lawful basis) | https://gdpr-info.eu/art-6-gdpr/ |
| GDPR Art. 83 (penalties) | https://gdpr-info.eu/art-83-gdpr/ |
| EU SCCs (2021) | https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/standard-contractual-clauses-scc_en |
| UK GDPR / DPA 2018 | https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/ |
| UK IDTA | https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/ |
| CCPA (CA AG) | https://oag.ca.gov/privacy/ccpa |
| CPRA regulations | https://cppa.ca.gov/regulations/ |
| Zoom Terms of Service | https://www.zoom.com/en/trust/terms/ |
| Zoom AUG | https://explore.zoom.us/en/trust/legal-compliance/ |
| Microsoft Services Agreement | https://www.microsoft.com/en-us/servicesagreement/ |
| Teams Compliance Recording | https://learn.microsoft.com/en-us/microsoftteams/teams-recording-compliance |
| Google Meet AUP | https://support.google.com/meet/answer/9847091 |
| Google Meet Media API | https://knowledge.workspace.google.com/admin/meet/control-media-api-access-in-google-meet |
| OpenAI DPA | https://openai.com/policies/data-processing-addendum |
| Deepgram Legal | https://deepgram.com/legal |
| TechCrunch / Cluely (2025) | https://techcrunch.com/2025/04/21/columbia-student-suspended-over-interview-cheating-tool-raises-5-3m-to-cheat-on-everything/ |

---

## Appendix B — Recommended Immediate Action Items

Priority-ordered actions for the legal and product teams:

1. **[IMMEDIATE — Legal]** Commission a formal legal opinion from a wiretapping specialist in at minimum CA, FL, IL, PA, and WA before any live-interview feature ships.
2. **[IMMEDIATE — Product]** Disable system loopback audio capture from any production build; restrict to candidate-microphone-only or post-session processing.
3. **[IMMEDIATE — Legal]** Draft and execute DPAs with Deepgram and OpenAI; confirm zero-data-retention and no-training-use provisions.
4. **[30 days — Legal]** Draft compliant Terms of Service and Privacy Policy; engage GDPR counsel for EU/UK compliance review.
5. **[30 days — Product]** Implement per-session consent gate with jurisdiction display and acknowledgment logging.
6. **[30 days — Product]** Implement geo-jurisdiction detection and feature restriction for all-party consent states and EU/UK.
7. **[60 days — Legal]** Complete a DPIA before any EU/UK user launch.
8. **[60 days — Product/Legal]** Publish Ethics and Responsible Use Policy; update marketing to reflect "practice and prep" framing.
9. **[90 days — Engineering]** Achieve SOC 2 Type II readiness; implement secrets scanning and security controls informed by the Cluely breach post-mortem.
10. **[Ongoing — Legal]** Quarterly review of Zoom, Teams, and Google Meet ToS/AUP changes; assign ownership.

---

*This brief was prepared for internal legal advisory purposes as of August 13, 2026. Laws and platform policies in this space are evolving rapidly; this document should be reviewed and updated at least quarterly. This brief does not constitute legal advice and should be reviewed by qualified legal counsel in each jurisdiction in which the product operates.*

---

## Research Notes and Source Transparency

Here is a summary of what was directly fetched and verified vs. what was synthesized from authoritative secondary sources:

**Directly fetched and verified:**
- **Google Meet AUP** (support.google.com/meet/answer/9847091, last updated Sept 11, 2025): The Circumvention, Deceptive Practices, and System Interference clauses are directly quoted from the live document.
- **Google General Terms of Service** (policies.google.com/terms): The "Don't abuse our services" and "Respect others / privacy rights" sections confirmed.
- **Zoom Terms of Service** (zoom.com/en/trust/terms/): Sections 1–3 confirmed live; Section 4 AUP language sourced via authoritative web search against Zoom's own trust/legal pages.

**Verified via authoritative web search with citations:**
- **Zoom AUP Section 4** language (intercept, eavesdrop, scrape, PII without consent) — confirmed via search against Zoom's own trust center documentation.
- **Microsoft Teams bot-blocking** (as of July 2026) — confirmed via UCToday and voip.review reporting on Microsoft's formal policy rollout.
- **State recording law statutes** — confirmed via recordinglaw.com, Justia 50-state survey, and direct statute citations.
- **GDPR Articles 3, 5, 6, 13, 14, 17, 21, 35, 83** — confirmed via gdpr-info.eu (official consolidated text).
- **Cal. Penal Code § 632** penalties — confirmed via california.public.law and Shouselaw.com analysis.
- **Cluely controversy / Columbia suspension** — confirmed via TechCrunch April 2025 reporting and Cybernews.
- **OpenAI and Deepgram DPAs** — confirmed via openai.com/policies/data-processing-addendum and conductatlas.com analysis.
