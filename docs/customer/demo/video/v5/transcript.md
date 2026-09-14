# NetMamba+ — both CSVs, both repositories, one packet workflow — transcript

Synthetic narration rendered from reviewed text. This video explains recorded experiments; it does not perform new training or live capture.

Runtime: 01:00:00, including 02:00 of labeled practice pauses. Caption timing: Speech-service word boundaries mapped through the final audio timing; independent encoded-audio checks are reported separately. Full human listening and caption-alignment review remain pending.

Author: Codex · Director: Codex · Narration role: Microsoft Andrew neural voice renders Codex-authored text through edge-tts; it does not author the lesson. · Text authorship: Codex authored and reviewed the lesson; no local language model wrote the narration. · Human full watch: not performed; automated and model-assisted audits are reported separately

## 00:00:00 — The client problem and the two repositories

### 00:00:00 — Follow one packet to a decision

Imagine a client asking what this project actually does. Computers send information in small units called packets. This project takes the recorded content of one packet and gives it scores for two supplied categories: benign and attack. Benign is the category used for ordinary traffic in these examples. Attack is the other training category. The model learns patterns in numerical examples; it does not investigate an incident or know the customer's business. Our job throughout this video is to connect that simple description to the files, the trained model, and the evidence behind its measured behavior.

On screen: Stored packet bytes · Trained numerical model · Benign or attack scores

Evidence: [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md)

### 00:00:38 — The paper, the implementation, and the evidence

Three things play different roles here. The research paper explains a proposed method, much as a recipe explains how a dish could be made. The repository contains the programs and instructions used to put the method into practice. The evidence records what happened when those programs were run. The two uploaded tables supply the packet examples. They are not instructions, and the paper is not fed into the classifier. When presenting a result to a client, connect the claim to the matching evidence. A diagram explains an idea; a saved measurement supports a claim about an executed experiment.

On screen: Paper: research method · Repository: executable work · Evidence: recorded outcomes

Evidence: [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [paper-notes](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/paper-and-data-explained.md), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md)

| Supplied file | Role in the project |
| --- | --- |
| 2601.21792v1.pdf | Method to inspect; never model input |
| Payload_data_CICIDS2017.csv | CIC packet bytes and labels |
| Payload_data_UNSW.csv | UNSW packet bytes and labels |

### 00:01:16 — One supported route from both CSVs

Follow the same route whenever you explain or run the client delivery. Start with both supplied packet files, the C I C I D S twenty seventeen export and the U N S W export. Preparation checks their contents and organizes repeated packet payloads. Training then uses selected examples from both sources. Validation chooses the saved version that will be used for prediction. That chosen classifier is called the joint pretrained model. Later, a separate unlabeled packet file goes through that saved model to produce scores. Every step in this course belongs to that single supported packet workflow.

On screen: Both uploaded CSVs · Prepare and train packet adaptation · Use the joint pretrained model

Evidence: [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [packet-data](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_data.py)

### 00:01:57 — What joint pretrained means

The model's name tells you two useful facts. Joint means that its supervised training includes examples from both uploaded sources. Pretrained means that the central encoder begins with released weights learned earlier. An encoder turns input numbers into a representation that later layers can use. A new final layer learns the two packet categories. The released initialization file is not the finished joint classifier. The repository also trained comparison models and simpler controls to investigate this choice. Those experiments help explain the evidence. They do not give the client several competing setup routes. For the supported demonstration and prediction commands, we use the validation selected joint pretrained classifier.

On screen: Joint: examples from both sources · Pretrained: transferred starting weights · One selected packet classifier

Evidence: [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [packet-protocol](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/protocol.json)

### 00:02:45 — Learning a rule and using a saved rule

Think of training as practice with an answer key. The model makes a prediction, compares it with the supplied answers, and adjusts numbers called weights. A checkpoint saves those learned numbers together with information needed to interpret them. Inference means using a selected checkpoint while keeping its weights fixed. It resembles applying an established rule to another example. During inference the packet bytes are available, but the true answer need not be. Without a known answer, we can report a prediction, but we cannot measure whether that prediction was correct. Downloading source code alone does not supply a trained checkpoint.

On screen: Training changes weights · Checkpoint saves a model · Inference applies fixed weights

Evidence: [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md)

### 00:03:24 — Two repositories, one packet workflow

There are two repositories because different readers need different packages. Net Mamba Plus reproduction is the full development, research, and learning source. It includes the implementation, measured evidence, explanations, and teaching media. Net Mamba Plus client is the concise executable delivery, with setup instructions, packet programs, tests, and the packet evidence needed for handoff. The client edition omits the teaching videos, PowerPoint decks, and presenter scripts. Both describe the same packet model workflow. The client has separate Git history and receives verified exports; its client manifest identifies the source revision and delivered files. Send the client repository together with the client project guide. Use the reproduction repository when someone wants to understand the broader development and teaching record.

On screen: Full source and teaching record · Concise executable client delivery

Evidence: [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md)

| Repository | Purpose |
| --- | --- |
| netmambaplus-reproduction | Development, research, evidence, media |
| netmambaplus-client | Setup, execution, tests, packet evidence |

### 00:04:19 — Explain the delivered capability precisely

A useful client explanation separates a working capability from the environment around it. This delivery contains runnable packet classification, verification tools, and an offline viewer of recorded predictions. The viewer helps inspect the experiment; opening it does not capture traffic or run fresh model inference. The measured results describe selected examples from the supplied exports. They do not establish detection quality on every real network. As we continue, keep following one question: what enters each step, what leaves it, and which saved record supports that description? That habit lets you explain the repository confidently without needing to become its programmer.

On screen: Runnable packet classification · Saved evidence and offline viewer · Performance tied to the tested exports

Evidence: [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md)

### 00:05:06 — Explain it back

**Practice pause: 10 seconds.** Explain the packet route and the purpose of each repository.

On screen: Explain the packet route and the purpose of each repository.

Evidence: [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md)

## 00:05:16 — The paper's idea and our packet adaptation

### 00:05:16 — Three views of traffic in the paper

The paper asks how a model can classify network traffic while processing sequences efficiently. Its Net Mamba Plus representation combines three views of related traffic. Bytes represent recorded content. Packet sizes describe how large the pieces are. Arrival intervals describe the gaps between them. Imagine observing deliveries: what each package contains, how large it is, and how deliveries are spaced can provide different clues. The technical word multimodal means these multiple traffic views. It does not mean a conversation involving pictures and audio. Before copying an architecture diagram, we must check which of those observations our actual data can support.

On screen: Bytes: recorded content · Sizes: packet lengths · Timing: arrival intervals

Evidence: [paper-notes](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/paper-and-data-explained.md), [upstream-comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md)

### 00:05:58 — Mamba carries a numerical state forward

Mamba is a selective state space model. The name sounds difficult, but begin with a simple picture: reading a sequence while continually updating a small numerical notebook. The notebook is the state. Each new input influences how that state changes and which information is carried forward. Selective means that this behavior depends on the input, using learned calculations. The notebook analogy explains information flow; the actual state is a collection of numbers. It is neither written reasoning nor a live connection database. In our project this encoder processes packet byte representations, then passes useful numerical summaries to a classifier.

On screen: Read the next input · Update a learned state · Carry information onward

Evidence: [paper-notes](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/paper-and-data-explained.md), [upstream-comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md)

### 00:06:41 — A packet row cannot establish a whole flow

The paper's flow representation groups related packets according to connection and ordering rules. Picture sorting letters into conversations: you need reliable information about who wrote to whom and which message came first. The supplied packet tables lack the addresses, ports, connection identifiers, and established ordering needed for that reconstruction. Five neighboring spreadsheet rows might describe unrelated conversations. Matching their labels or protocol names does not repair the missing information. Even the recorded time difference has an undocumented interpretation. We therefore treat each row's stored payload as one packet example. This explicit choice determines what the resulting measurements can mean.

On screen: Packet: one network unit · Flow: related packets with defined order · Connection and ordering evidence are missing

Evidence: [paper-notes](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/paper-and-data-explained.md), [csv-profile](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/uploaded-csv-profile.json), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md)

### 00:07:28 — Pretraining learns to reconstruct hidden content

Think of pretraining as practice with part of each example hidden. The model sees the remaining information and tries to reconstruct what was hidden. Its answer key is the original input content, rather than an attack category. The reconstruction error guides adjustments to the weights. This can produce a useful starting representation before a later classification task has been learned. Our packet model loads the encoder weights released by the paper's authors. We did not recreate their complete earlier training corpus. The checkpoint's full exposure history remains unknown, so transferring those weights does not establish that earlier examples were independent.

On screen: Hide selected input content · Predict what was hidden · Adjust the encoder's weights

Evidence: [paper-notes](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/paper-and-data-explained.md), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md)

### 00:08:10 — Supervised learning teaches the packet categories

Supervised classification asks a different question from reconstruction. Instead of filling in missing input content, the model learns which supplied category belongs with an example. Here those categories are benign and attack. The pretrained encoder provides a starting point, and a fresh classification head learns how to turn its summaries into two scores. A head is simply the final decision layer. During training the known labels guide weight changes; they are not inserted into the encoder's input. This distinction matters when explaining the research connection: we reuse the learning machinery while adapting its observation unit and its final classification task.

On screen: Packet bytes enter the encoder · New head produces two scores · Supplied labels guide training

Evidence: [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [upstream-comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md)

### 00:08:52 — What the packet adaptation actually observes

In the packet adaptation, the actual observations are the fifteen hundred stored payload bytes. The size and timing branches contain no observed sequences. Two learned prefix components remain, but they are model parameters, not measurements taken from the spreadsheet. The recorded time to live, length, protocol, time difference, dataset identity, and label never enter the neural forward pass, meaning the calculation that produces its scores. Metadata is examined separately and used in diagnostic controls. This is why a drawing with three traffic views needs a careful caption: it describes the paper's architecture, while this adaptation supplies only the packet bytes.

On screen: All 1,500 stored payload bytes · No observed size or interval sequences · Metadata stays outside the neural call

Evidence: [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [packet-protocol](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/protocol.json)

### 00:09:36 — A similar percentage is not the same experiment

The paper reports ninety seven point five zero percent flow accuracy on C I C I o T twenty twenty two in Table Four. That dataset is different from the uploaded C I C I D S twenty seventeen export. Our packet study measures a different observation unit, different data, a binary target, and group weighted balanced accuracy. Balanced accuracy averages how well the two categories are recovered. Ordinary accuracy counts the overall fraction correct. Similar percentages do not make those measurements interchangeable. The repository has not reproduced the paper's flow result through these CSVs. When a client asks whether the adaptation matches the paper, explain the changed task first. Likewise, the paper's efficiency or deployment claims do not automatically describe our checked GPU execution.

On screen: Paper Table IV: 97.50% CICIoT2022 flow accuracy · Packet study: a different task and metric · Compare the conditions before the numbers

Evidence: [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [paper-notes](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/paper-and-data-explained.md), [upstream-comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md)

### 00:10:34 — Explain it back

**Practice pause: 10 seconds.** Why is this a packet adaptation rather than the paper's flow experiment?

On screen: Why is this a packet adaptation rather than the paper's flow experiment?

Evidence: [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [paper-notes](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/paper-and-data-explained.md)

## 00:10:44 — Read the CICIDS2017 packet CSV

### 00:10:44 — A text table of packet examples

Now open the first source conceptually, as though we were looking across a very wide spreadsheet. C S V means comma separated values, a text format containing rows and columns. This supplied C I C I D S twenty seventeen export contains one million, four hundred ten thousand, two hundred fifty five packet rows and fifteen original labels. Each row is one stored packet example. The row count does not count connections, distinct payloads, or successful predictions. The dataset name identifies the supplied export under study; it does not establish every detail of how that export was originally produced.

On screen: CICIDS2017 supplied export · 1,410,255 packet rows · 15 original labels

Evidence: [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [paper-notes](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/paper-and-data-explained.md), [csv-profile](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/uploaded-csv-profile.json), [packet-manifest](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/manifest.json)

### 00:11:27 — Read one row in three parts

Move across a single row from left to right. The first fifteen hundred columns are ordered payload byte slots. They are followed by four metadata fields and then the label, giving fifteen hundred and five columns altogether. Metadata means recorded information about the example. The label is its supplied answer. Keep these three roles separate even though the spreadsheet places them side by side. The preparation code expects the exact header sequence, so swapping columns changes the input contract. Fifteen hundred byte columns describe positions within one packet representation; they are not fifteen hundred independent packets or separate training examples.

On screen: One row represents one packet example · 1,505 columns in a fixed order

Evidence: [paper-notes](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/paper-and-data-explained.md), [packet-data](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_data.py), [packet-manifest](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/manifest.json)

| Part | Contents |
| --- | --- |
| Payload | 1,500 ordered byte slots |
| Metadata | ttl, total_len, protocol, t_delta |
| Target | label |

### 00:12:08 — Byte slots contain numbers, including stored zeros

A byte is a small numerical value from zero through two hundred fifty five. In the CSV it is written as text, and preparation checks that it represents an exact valid integer before conversion. Think of an ordered strip of numbered tiles. The model receives the strip's numerical pattern; this is not a promise to translate its contents into readable messages. A tile containing zero is still part of the stored representation. The export does not reliably identify which zeros are padding. We preserve all the stored slots, rather than guessing that a zero or recorded length justifies removing them.

On screen: Integer values from 0 through 255 · Exact order is preserved · Stored zeros remain in the input

Evidence: [packet-data](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_data.py), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [paper-notes](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/paper-and-data-explained.md), [packet-manifest](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/manifest.json)

### 00:12:47 — Four recorded properties, with specific limits

The next fields describe recorded properties. Time to live relates to a packet's lifetime across the network. Total length records a packet length, but does not identify meaningful payload slots. Protocol records a carrying category such as T C P or U D P; it is not an attack answer. Time delta records a difference whose units and reference event are not established here. These values are profiled, and the separate metadata controls validate and use them. They never enter the native packet classifier. None supplies the missing connection identity or proves how neighboring rows should be ordered.

On screen: Profiled and checked for separate controls · Never inputs to the native neural call

Evidence: [paper-notes](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/paper-and-data-explained.md), [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [packet-protocol](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/protocol.json), [packet-manifest](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/manifest.json)

| Field | Recorded meaning |
| --- | --- |
| ttl | Time to live; network lifetime field |
| total_len | Recorded packet length |
| protocol | Traffic carrying protocol |
| t_delta | Time difference; interpretation unestablished |

### 00:13:28 — Keep the answer outside the model input

The last column supplies the example's label. In this source, the registered label benign maps to class zero. The other explicitly registered labels map to class one, attack. Unknown spellings are rejected instead of silently becoming an attack example. During supervised training, these answers guide learning after the model produces its scores. Giving the answer to the model as an input would defeat the purpose, like leaving the solution printed on an exam question. Later, known labels can score held out predictions. The separate prediction command requires an unlabeled input, so its model must decide from the stored bytes alone.

On screen: BENIGN maps to benign, class 0 · Registered attack labels map to class 1 · Unknown labels fail validation

Evidence: [packet-data](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_data.py), [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [packet-manifest](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/manifest.json)

### 00:14:10 — Many rows repeat the same stored payload

A large spreadsheet can repeat the same input many times. In this source, the original rows reduce to four hundred thirty eight thousand, eight hundred eighty six distinct stored payload groups. A group collects rows whose entire payload byte sequence is identical. Imagine receiving repeated photocopies of the same page: counting copies and counting distinct pages answer different questions. Preparation keeps the original label counts within each group, including disagreements. It does not pretend that repeated rows supply the same diversity as new payloads. This distinction will matter both when dividing the data and when interpreting a model's reported score.

On screen: 1,410,255 rows · 438,886 distinct payload groups · Every original label count is retained

Evidence: [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [packet-data](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_data.py), [packet-manifest](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/manifest.json)

### 00:14:54 — Check what the selected test set contains

Support means how many examples actually stand behind a measurement. The export has fifteen original categories, but that does not guarantee useful test coverage for every one. After duplicate grouping and the study's selection limits, the selected C I C test set contains no port scan rows and only four distributed denial of service rows. We therefore have no measured port scan performance there, and four rows cannot support a broad claim about distributed attacks. Preparation accounts for the whole file, while training uses selected and sampled groups. Always ask what reached the relevant experiment, not just what arrived originally.

On screen: Counts are not performance · No PortScan test rows · Four DDoS test rows

Evidence: [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [packet-protocol](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/protocol.json), [packet-manifest](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/manifest.json)

### 00:15:36 — Explain it back

**Practice pause: 10 seconds.** Explain the three parts of a row and which part reaches the model.

On screen: Explain the three parts of a row and which part reaches the model.

Evidence: [packet-data](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_data.py), [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [packet-manifest](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/manifest.json)

## 00:15:46 — Add UNSW and protect the experiment's split

### 00:15:46 — UNSW uses the same row structure

The second supplied export, U N S W, contains seventy nine thousand, eight hundred eighty one packet rows and ten original labels. Its rows follow exactly the same column structure as the first file: fifteen hundred payload byte slots, four metadata fields, and a label. That shared structure makes a common packet preparation route possible. The examples and original category vocabulary are different. For instance, ordinary traffic is labeled normal here, while other registered names include generic and exploits. A familiar table layout is useful compatibility evidence, but it does not make the underlying traffic or its supplied annotations identical.

On screen: 79,881 packet rows · The same 1,505-column schema · 10 original labels

Evidence: [csv-profile](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/uploaded-csv-profile.json), [paper-notes](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/paper-and-data-explained.md), [packet-data](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_data.py), [packet-manifest](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/manifest.json)

### 00:16:30 — Map source labels to the shared binary task

To train one binary classifier, preparation gives both sources a shared target definition. C I C's benign label and U N S W's normal label become the benign category. The other registered labels become attack. This mapping creates a compatible learning question; it does not assert that all the original attack names mean the same thing. Their source names and counts remain available for analysis. Dataset identity stays outside the neural forward pass. We have also not independently established that every supplied annotation reflects operational maliciousness. The model learns the provided labeling task, with those limits carried into its evaluation.

On screen: Keep original source annotations · Use one benign or attack target

Evidence: [packet-data](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_data.py), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [packet-manifest](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/manifest.json)

| Source | Benign | Attack |
| --- | --- | --- |
| CICIDS2017 | BENIGN | Other registered CIC labels |
| UNSW | normal | Other registered UNSW labels |

### 00:17:15 — Combine packet examples without inventing connections

Combining the files means bringing compatible packet examples into the same study. Conceptually, we place their example collections together, while preserving the source records. We do not match row one in one file with row one in the other, or append one packet's bytes to another packet's bytes. That would invent a relationship the data never established. The joint training procedure draws selected groups from both sources to teach one classifier. Think of combining two sets of practice cards that ask the same kind of question. Each card remains a separate example, even though both sets contribute to learning.

On screen: Compatible examples from both sources · Shared preparation and grouping · Joint packet training

Evidence: [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [packet-data](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_data.py), [packet-protocol](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/protocol.json), [packet-manifest](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/manifest.json)

### 00:17:54 — Find exact payload duplicates across both sources

Duplicate checking must cover both files together. The complete preparation identifies four hundred seventy eight thousand, forty four globally distinct payloads. Global means the same stored bytes count as one identity even if they appear in different sources. The code computes a fingerprint called S H A two fifty six from all fifteen hundred canonical bytes. This provides a practical identity for grouping exact payloads, and the preparation checks matching payload content. Original row counts and source labels remain associated with that identity. A fingerprint describes exact stored content; it does not reveal which physical connection or capture produced it.

On screen: Compare all 1,500 stored bytes · Assign a SHA-256 fingerprint · 478,044 global payload groups

Evidence: [packet-data](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_data.py), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [packet-manifest](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/manifest.json)

### 00:18:38 — Shared payloads can carry conflicting answers

Ten exact payloads appear in both supplied files. Nine of those shared payloads have conflicting binary labels. That means identical model input can be associated with benign in some rows and attack in others. The model is missing the context that might explain the difference, and the labels have not been independently adjudicated. We do not fix this by deleting the inconvenient answer or declaring one source correct. The original counts remain visible. These nine are the conflicting groups among the shared payloads; this is not a claim that the whole combined dataset contains only nine disagreements of this kind.

On screen: 10 payloads appear in both files · 9 of those have conflicting binary labels · Disagreements remain in the evidence

Evidence: [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [packet-data](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_data.py), [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [packet-manifest](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/manifest.json)

### 00:19:17 — Preserve disagreement as label proportions

Use an illustrative group to see how the training handles disagreement. Suppose identical bytes occur in nine rows labeled benign and one row labeled attack. The group's target is ninety percent benign and ten percent attack. Those are proportions of supplied labels, not a newly verified probability about network behavior. Each sampled group has equal total weight in the learning calculation, with that weight divided according to its answers. This preserves the contradiction while preventing a highly repeated payload from automatically dominating the training loss. Later, the evidence can distinguish weighting original rows from giving each payload one total vote.

On screen: Illustration: nine benign rows, one attack row · Training target: 90% benign, 10% attack · Each sampled group has equal total weight

Evidence: [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [packet-protocol](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/protocol.json), [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [packet-manifest](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/manifest.json)

### 00:20:01 — Keep exact duplicates inside one partition

Each global payload group receives a partition through a hash rule using split seed seventeen. Training groups teach the weights. Validation groups select the saved checkpoint. Test groups measure it after selection has frozen. The target proportions are seventy, fifteen, and fifteen percent, with later caps selecting groups inside those partitions. Keeping identical payloads together prevents exact copies from leaking from practice into the exam, including across both sources. The animated symbols represent whole groups that stay intact. This does not remove every near duplicate or prove capture independence. These results describe the defined export study, not guaranteed performance on a client's network.

On screen: Group first, using both sources · Seed 17: target 70% / 15% / 15% · Train, validation, and test stay distinct

Evidence: [packet-data](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_data.py), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [packet-manifest](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/manifest.json)

Exact payloads: Same bytes stay together
Train: Target 70% · learn weights
Validation: Target 15% · select checkpoint
Test: Target 15% · measure afterward
Seed 17 · target proportions before caps · identical payloads stay in one split; capture independence unknown.

### 00:20:49 — Explain it back

**Practice pause: 10 seconds.** Why group both sources before splitting, and what uncertainty remains?

On screen: Why group both sources before splitting, and what uncertainty remains?

Evidence: [packet-data](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_data.py), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [packet-manifest](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/manifest.json)

## 00:20:59 — Follow one packet through the model

### 00:20:59 — One packet supplies the model input

Follow one table row from the supplied CSV into the classifier. Its payload contains fifteen hundred stored bytes in a fixed order. These bytes are the observation available to the model, and changing their order can change the pattern. The metadata records length, time to live, protocol, and time delta, but stays outside neural input. The classifier receives only the transformed payload. During training, a label supplies the answer used to score its prediction afterward. Source identity and that answer never enter the forward calculation. The diagram separates the branches so you can point to exactly what informs a prediction.

On screen: 1,500 ordered stored bytes per packet · Metadata stays outside neural forward · Labels are targets, never model features

Evidence: [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [packet-model](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_model.py), [packet-data](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_data.py)

CSV row: Bytes + context + label
Payload: 1,500 stored bytes
Metadata: Ignored by neural input
Classifier: Receives payload only
Illustrative data path · supplied labels affect training loss, never model input.

### 00:21:41 — Rescale the bytes without changing their order

The adapter converts the validated bytes into floating point numbers, which can represent fractions. It divides each byte by one hundred twenty seven point five and subtracts one. Zero becomes negative one, and two hundred fifty five becomes positive one. This changes the numerical scale while preserving the byte order. A tensor is an array with named dimensions in our explanation: the batch, two dimensions of size one, and fifteen hundred byte positions. Stored zeros remain because the export does not establish which zeros represent padding. Removing them would silently change the observation supplied to this model.

On screen: Byte 0 becomes −1; byte 255 becomes +1 · Tensor: batch × 1 × 1 × 1,500 · Stored zeros remain in the input

Evidence: [packet-model](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_model.py), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md)

```text
batch = payload_tensor.shape[0]
byte_stream = (
    payload_tensor.to(dtype=torch.float32) / 127.5 - 1
).reshape(batch, 1, 1, 1500)
```

### 00:22:21 — Assemble 378 tokens from one packet

Start with fifteen hundred bytes from one packet. Grouping and embedding turn each four neighboring bytes into one learned vector, producing three hundred seventy five vectors. The assembled sequence adds three learned tokens, bringing its length to three hundred seventy eight. Each position contains two hundred fifty six numerical coordinates. Four Mamba blocks transform that sequence using the original encoder machinery. Finally, class logits provide two scores after the summary outputs are added and passed through the binary head. These are numerical processing stages, not words in a language model. The animation is a schematic of the computation, not a live execution.

On screen: 1,500 ordered bytes · 375 vectors from groups of 4 bytes · 3 learned tokens → 378 tokens × 256 values

Evidence: [packet-model](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_model.py), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md)

Bytes: 1,500 positions
Embed: Groups of 4 375 vectors
Sequence: +3 → 378 × 256
Mamba: 4 native blocks
Output: 2 class logits
Packet adaptation · 375 byte vectors + 3 learned tokens; empty size and timing observations.

### 00:23:07 — Empty streams still have learned prefixes

The size stream contains no observations, and the interval stream also contains no observations. Interval means a gap between arrivals; these CSVs do not establish the flow timing needed for that input. Their two learned prefixes remain trainable model parameters, beginning identically for each packet. The native encoder scans in a causal order, meaning earlier positions cannot read later positions. These prefix outputs therefore cannot summarize bytes that appear afterward, although later byte positions can use the prefixes. Calling all three positions summaries of the packet would conceal this distinction. Empty streams are an explicit part of the adaptation.

On screen: Size observations: 0; interval observations: 0 · Two learned prefixes begin identically for each packet · Prefix outputs cannot summarize later bytes

Evidence: [packet-model](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_model.py), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [initialization](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/initialization-audit.json)

### 00:23:51 — Four blocks lead to two class scores

The sequence enters four native Mamba blocks. Each block updates a learned numerical state as it processes the ordered representation. The fusion step adds the three designated output vectors, and the binary head turns that combined vector into two logits. A head is the final scoring layer; a logit is a raw class score. One score represents benign and the other attack. Across the full packet classifier there are one million eight hundred fifty two thousand four hundred sixteen parameters, the adjustable numbers learned during training. These parameters are different from the changing byte values in each incoming observation.

On screen: 4 native Mamba blocks · Add the 3 output summary vectors · Binary head → benign and attack logits

Evidence: [packet-model](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_model.py), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md)

### 00:24:31 — Transfer compatible weights into the packet model

Pretrained initialization starts with useful numerical settings from the authors' released checkpoint. The adapter copies fifty compatible model tensors and excludes thirty one tensors used for reconstructing hidden inputs. A tensor here is a stored array of parameters. The binary head starts fresh. Learned position values are explicitly selected from the original table, mapping three hundred seventy eight positions from four hundred forty three. Scratch initialization uses the same coordinates from fresh weights. This preserves a defined comparison, while the shorter byte sequence and empty numeric streams keep the packet experiment distinct from the paper's flow experiment.

On screen: Reuse compatible encoder state; start a fresh binary head · Learned positions remain trainable

Evidence: [packet-model](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_model.py), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [initialization](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/initialization-audit.json)

| Component | Packet treatment |
| --- | --- |
| Compatible trunk tensors | 50 copied |
| Reconstruction tensors | 31 excluded |
| Binary head | Fresh weights |
| Position table | 378 selected from 443; trainable |

Position indices: [20, 41] + range(42, 417) + [442].

### 00:25:14 — Explain the complete feature path

Now connect the pieces in ordinary language. One packet supplies ordered stored bytes; those bytes are rescaled and grouped into learned vectors. Three learned tokens join the sequence, four encoder blocks process it, and a binary head produces the final scores. The optional metadata has not joined that journey. The label helps training judge a prediction, but does not enter the forward calculation that produces it. This model performs numerical traffic classification without calling a chat service. Use the coming pause to explain both the information it receives and the information its input contract deliberately leaves outside.

On screen: Describe the stored bytes and their transformation · Identify learned tokens and empty streams · Separate model inputs from training answers

Evidence: [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [packet-model](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_model.py), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md)

### 00:25:56 — Your turn · 10 seconds

**Practice pause: 10 seconds.** Explain how one packet becomes two scores, including what stays outside.

On screen: Explain how one packet becomes two scores, including what stays outside.

Evidence: [packet-model](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_model.py), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md)

## 00:26:06 — Understand how the packet model learns

### 00:26:06 — Preserve disagreements in the learning target

Training begins with supplied answers, including their disagreements. Imagine one identical payload recorded nine times as benign and once as attack. The group receives a soft target of ninety percent benign and ten percent attack. Soft means the answer preserves proportions instead of forcing one label to win. When that group is sampled, its total contribution to the learning loss is one group, divided according to those proportions. Repeated copies do not acquire extra total influence simply by being numerous.

On screen: Same payload: 9 benign labels + 1 attack label · Soft target: 90% benign / 10% attack · One sampled group contributes one total weight

Evidence: [packet-data](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_data.py), [packet-training](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/train_packet_model.py), [packet-protocol](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/protocol.json)

### 00:26:41 — Compare six training arms

An experimental arm is one defined training comparison. Here the source choice is C I C alone, U N S W alone, or both together. Each choice runs with transferred pretrained weights and with fresh scratch weights, giving six arms. All use the same packet architecture and one model seed, zero. A seed fixes the recorded random choices for this run. Paired pretrained and scratch arms have identical fresh heads and sampled groups, helping isolate the initialization comparison. One seed still gives only one observed run per arm; it does not describe variation across many independently repeated training runs.

On screen: Three source choices × two initializations · One model seed: 0 · Paired arms share fresh heads and sampled groups

Evidence: [packet-protocol](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/protocol.json), [packet-model](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_model.py), [packet-training](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/train_packet_model.py)

| Training source | Transferred initialization | Fresh initialization |
| --- | --- | --- |
| CIC only | cic_pretrained | cic_scratch |
| UNSW only | unsw_pretrained | unsw_scratch |
| CIC + UNSW | joint_pretrained | joint_scratch |

### 00:27:23 — One update is one learning step

One update means one cycle through this diagram. Sample sixty four training groups, with replacement. The forward calculation produces two scores for each payload. The loss compares those scores with the supplied label proportions. Backward computation finds gradients, numbers that describe how weight changes could reduce that loss. The optimizer then changes the weights, completing the update. Joint batches contain thirty two groups from each source. Every arm completed one thousand updates, or sixty four thousand group presentations. Repeatedly presenting the same group is allowed. An update is not an epoch over the complete uploaded tables, and it does not modify the labels.

On screen: Sample a batch of 64 groups · Compare predictions with group targets · Update weights; complete 1,000 updates

Evidence: [packet-training](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/train_packet_model.py), [packet-protocol](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/protocol.json), [packet-results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/results.json)

Forward: Payload → two scores
Loss: Compare with soft targets
Backward: Calculate gradients
Update: Optimizer changes weights
Recorded protocol: 1,000 updates per arm · batch 64 · replacement sampling.

### 00:28:08 — Caps and replacement sampling define exposure

The selected training pool contains one hundred thousand C I C groups and twenty seven thousand three hundred eighty U N S W groups. Joint batches draw thirty two from each source, keeping the two sources equally represented within each batch. Sampling uses replacement, which means a group can appear again while another selected group never appears. Across one thousand updates, each model receives sixty four thousand group presentations. An epoch would mean a pass through a defined training dataset. These presentations are not full CSV epochs, and validating all original rows does not mean training on all of them.

On screen: Joint batches: 32 groups from each source · Sampling with replacement can repeat a group · 64,000 presentations per model, not full CSV epochs

Evidence: [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [packet-training](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/train_packet_model.py), [packet-protocol](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/protocol.json)

| Source | Selected training groups | Groups per joint batch |
| --- | --- | --- |
| CIC | 100,000 | 32 |
| UNSW | 27,380 | 32 |

### 00:28:50 — Validation chooses; frozen test groups measure

Validation runs every hundred updates, using groups separate from training. Its selection score is group weighted macro F one: a measure that combines precision and recall for each class and averages the two classes. Precision asks how often a predicted class is correct; recall asks how much of that class was found. Joint selection averages the two source scores. The earliest checkpoint with the best score wins any tie. All six selections freeze before the final test predictions. This order lets test groups measure the selected models without using their answers to choose which checkpoint looks most attractive.

On screen: Validation every 100 updates · Select earliest best group macro-F1 · Freeze all selections before final test inference

Evidence: [packet-protocol](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/protocol.json), [packet-training](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/train_packet_model.py), [packet-results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/results.json)

### 00:29:30 — Freeze the experiment and retain its receipts

A frozen protocol records what experiment will be run before its final results are known. It binds the data manifest, original source identities, implementation files, sampling rules, and training budget. Binding means recording hashes that identify exact file contents. A hash can reveal a changed file, although it cannot prove that an annotation is true. Checkpoints preserve the relevant protocol and data identities alongside their weights. Training receipts record achieved updates, selection history, and optimizer counters. Those counters establish that training continued even when an earlier checkpoint was selected.

On screen: Protocol binds data, code, rules, and budget · Checkpoints retain selection and input identities · Receipts establish achieved optimizer updates

Evidence: [packet-protocol](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/protocol.json), [packet-model](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_model.py), [packet-training](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/train_packet_model.py)

### 00:30:12 — Distinguish training, selection, and inference

Before opening the code, explain three different uses of data. Training groups change model weights through repeated learning updates. Validation groups choose a saved checkpoint according to the rule fixed in advance. Inference applies selected weights to observations without another learning update; final test inference adds known answers only to calculate measurements. The client uses the joint pretrained selection, so both sources contributed supervised training examples. The separate split seed, seventeen, assigned payload groups to partitions; it is different from the model seed, zero. Use the pause to identify which stage changes weights, which chooses them, and which measures them.

On screen: Training groups change the weights · Validation groups choose saved weights · Inference applies a selected checkpoint

Evidence: [packet-data](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_data.py), [packet-protocol](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/protocol.json), [packet-training](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/train_packet_model.py), [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md)

### 00:30:58 — Your turn · 10 seconds

**Practice pause: 10 seconds.** Explain which data changes weights, chooses a checkpoint, and measures it.

On screen: Explain which data changes weights, chooses a checkpoint, and measures it.

Evidence: [packet-protocol](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/protocol.json), [packet-training](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/train_packet_model.py)

## 00:31:08 — Read the code behind training and prediction

### 00:31:08 — Find the five implementation responsibilities

The files divide the workflow into responsibilities that are easier to inspect separately. The data module validates the supplied tables and prepares payload groups. The model module connects packet bytes to the pinned native encoder and manages compatible checkpoints. Shared study utilities calculate measurements and handle evidence records. The training program runs the frozen comparisons and records their selected weights. The prediction program applies a selected checkpoint to an unlabeled CSV.

On screen: Follow data preparation through training to prediction · Shared metrics keep result arithmetic consistent

Evidence: [packet-data](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_data.py), [packet-model](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_model.py), [packet-training](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/train_packet_model.py), [packet-prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/predict_packets.py), [packet-review](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/review_packet_study.py)

| File | Responsibility |
| --- | --- |
| packet_data.py | Validate and prepare groups |
| packet_model.py | Native adapter and checkpoints |
| packet_study.py | Metrics and evidence utilities |
| tools/train_packet_model.py | Run the frozen training study |
| tools/predict_packets.py | Predict an unlabeled packet CSV |

### 00:31:40 — The forward call receives only payload tensors

A prepared batch becomes an unsigned byte tensor, meaning an array whose entries hold integers from zero through two hundred fifty five. Its dimensions are the batch size and fifteen hundred bytes. The forward call passes this payload tensor into the adapter and returns two logits per observation. The adapter handles normalization and constructs the empty numeric streams we already examined. The training answers exist in a different tensor and never enter this call.

On screen: Input: unsigned byte tensor, batch × 1,500 · Output: floating point logits, batch × 2 · Training targets stay outside this call

Evidence: [packet-model](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_model.py), [packet-training](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/train_packet_model.py)

```text
# payload: [batch, 1500], unsigned bytes
logits = packet_model.forward_payload(model, payload)['logits']
# logits: [batch, 2], floating point scores
```

### 00:32:09 — Loss, gradients, and an optimizer update

The learning loop first clears gradients left from the previous update. It obtains logits, then computes cross entropy against the soft targets. Cross entropy is the loss measuring how poorly the scores fit those target proportions. Backward calculation finds gradients: numerical sensitivities showing how parameter changes affect the loss. The optimizer uses them to update the model. The complete implementation also rejects invalid numerical values, limits gradient size, and checks that learning signals reach the byte embedding, every encoder block, and the head. Those checks establish an actual learning path; held out measurements still determine whether its predictions are useful.

On screen: Loss measures disagreement with soft targets · Gradients connect that loss to model parameters · The optimizer changes weights

Evidence: [packet-training](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/train_packet_model.py), [packet-protocol](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/protocol.json)

```text
optimizer.zero_grad(set_to_none=True)
logits = packet_model.forward_payload(model, payload)['logits']
loss = -(
    truth * torch.log_softmax(logits, dim=1)
).sum(dim=1).mean()
loss.backward()
optimizer.step()
```

### 00:32:55 — Load the selected checkpoint for inference

Read the joint pretrained selection from the frozen checkpoint record. That entry identifies the saved weights chosen by validation, including their file identity. The model loader strictly checks the packet architecture, expected parameter arrays, class mapping, and provenance, which records where the model came from. The prediction program then places the loaded model in evaluation mode and applies it without learning updates. This is why the released pretraining file cannot replace the selected packet checkpoint: the client needs the binary classifier produced by supervised training. Keeping the weights together with their identifying record makes a later prediction traceable.

On screen: Read Selected joint pretrained checkpoint · Strictly load weights and their metadata · Apply fixed weights to new packet bytes

Evidence: [packet-model](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_model.py), [packet-prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/predict_packets.py), [packet-training](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/train_packet_model.py), [client-setup](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/client/SETUP.md.in)

### 00:33:39 — Validate the CSV before publishing completion

The prediction CSV accepts fifteen hundred payload columns, optionally followed by the four metadata columns. A label column is rejected, so create a separate unlabeled copy. Header order, row width, and payload byte validity are checked. A cap of one hundred twenty eight limits predicted rows while the program still scans the entire file. Predictions may be computed during that scan; successful completion requires validation to finish. A malformed later row prevents a successful completed result even if earlier predictions were calculated. The receipt reports validated and predicted counts separately, so a capped run cannot claim prediction coverage it lacks.

On screen: Exact unlabeled header and valid byte cells are required · A prediction cap still scans the whole CSV · The receipt distinguishes validated rows from predictions

Evidence: [packet-prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/predict_packets.py), [client-setup](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/client/SETUP.md.in)

| Input layout | Accepted |
| --- | --- |
| 1,500 ordered payload columns | Yes |
| Payload columns + ttl,total_len,protocol,t_delta | Yes; metadata stays outside forward |
| Any header containing label | No |

Full input validation precedes a successful completion receipt, not the first prediction.

### 00:34:23 — Read class decisions and uncalibrated scores

Each prediction record includes the row identity, payload hash, two logits, class name, and probabilities. The larger logit chooses the class, with an exact tie assigned to benign. Softmax converts the logits into nonnegative numbers that sum to one; it does not supply independent evidence about the customer's network. These scores are uncalibrated, meaning their numerical size has not been established as a reliable frequency of real malicious events. The separate receipt ties outputs to input, checkpoint, and code identities.

On screen: logits: two finite raw scores · class_name: benign or attack · probabilities and receipt: scores plus run identity

Evidence: [packet-prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/predict_packets.py), [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md)

### 00:34:58 — Check native execution on the prepared packets

The native packet gate checks whether the actual model operates in the prepared environment. Its recorded run on G B ten passed seventeen tests with none skipped, using two stored payloads from each source. It exercises compatible weight transfer, tensor shapes, gradients, an optimizer update, and strict checkpoint loading after saving. Synthetic targets supply a controlled learning signal for these checks. They do not measure benchmark accuracy or repeat the six arm training study.

On screen: 17 native GB10 tests passed; 0 skipped · Stored payloads with synthetic targets test functionality

Evidence: [native-gate](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/research/packet-checks/native-receipt.json), [client-setup](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/client/SETUP.md.in), [packet-model](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_model.py)

```text
python tools/check_packet_runtime.py \
  --data runs/packet-data-new \
  --upstream upstream/NetMambaPlus \
  --initialization assets/checkpoints/fuse3_mamba.pth \
  --output runs/packet-runtime-new
```

### 00:35:31 — Your turn · 10 seconds

**Practice pause: 10 seconds.** Explain what a successful capped prediction receipt proves about the input.

On screen: Explain what a successful capped prediction receipt proves about the input.

Evidence: [packet-prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/predict_packets.py), [native-gate](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/research/packet-checks/native-receipt.json)

## 00:35:41 — Explain the measured results and their limits

### 00:35:41 — The selected joint model's measured results

Start with the delivered joint pretrained model. It reached ninety seven point five six percent group balanced accuracy on C I C and ninety four point two nine percent on U N S W. The test sets contain twenty thousand and five thousand nine hundred thirty distinct payload groups, respectively, totaling twenty five thousand nine hundred thirty predictions. These groups came from the partitions reserved earlier. The selected weights were already frozen. This ties the headline to a defined model, unit, and evaluation set. Carry those conditions with the percentages whenever you explain what the study established to another person.

On screen: Joint pretrained checkpoint selected before final tests · 25,930 distinct test payload groups in total

Evidence: [packet-results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/results.json), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md)

| Test source | Distinct groups | Group balanced accuracy |
| --- | --- | --- |
| CIC | 20,000 | 97.56% |
| UNSW | 5,930 | 94.29% |

All six native models were evaluated on these same source test groups.

### 00:36:22 — Class balance and duplicate weighting answer different things

Balanced accuracy averages benign recall and attack recall, giving the two classes equal importance. Recall means the fraction of a supplied class correctly recognized. Group weighting gives each distinct payload one total vote, divided across conflicting labels. Row weighting gives every original row a vote, so repeated payloads can change the outcome. With row weighting, the joint scores become ninety six point three one percent on C I C and eighty nine point two four on U N S W. The model has not changed between these calculations; the weights assigned to the evaluation observations have changed.

On screen: Balanced accuracy averages benign and attack recall · Group weight: one total vote per distinct payload · Row weight: one vote per original row

Evidence: [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [packet-results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/results.json), [packet-review](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/review_packet_study.py)

| Joint pretrained test | Group balanced accuracy | Row balanced accuracy |
| --- | --- | --- |
| CIC | 97.56% | 96.31% |
| UNSW | 94.29% | 89.24% |

### 00:37:03 — Pretrained models show transfer tradeoffs

Read each row as one trained model and each column as a test source. The C I C pretrained model performs strongly on its own source but reaches only fifty three point seven three percent on U N S W. Transfer means applying learned weights to another source without supervised fitting on that source. Joint training changes this comparison: against the corresponding pretrained source models, it gains one point zero seven percentage points on U N S W and loses one point one one on C I C. These are observed tradeoffs in this run, not a universal benefit.

On screen: Each row is one model; each column is a test source · Joint versus source models: +1.07 points UNSW, −1.11 CIC

Evidence: [packet-results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/results.json), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md)

| Pretrained training source | CIC test | UNSW test |
| --- | --- | --- |
| CIC only | 98.67% | 53.73% |
| UNSW only | 71.52% | 93.22% |
| Joint | 97.56% | 94.29% |

Every score in this table is group weighted balanced accuracy.

### 00:37:41 — All scratch arms trained; their outcomes were weak

Scratch models expose an important weak result in the completed study. The C I C only and U N S W only selections both score fifty percent balanced accuracy on both test sources. Their decisions stay in a single class: one class receives full recall and the other receives none, averaging to fifty percent. Both checkpoints were selected at update one hundred, although their training continued to one thousand. Joint scratch reaches fifty five point five seven percent on C I C and fifty percent on U N S W. Completed training therefore includes models that failed to discriminate usefully.

On screen: Every scratch arm completed 1,000 updates · Single-source selections made constant-class decisions

Evidence: [packet-results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/results.json), [packet-training](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/train_packet_model.py), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md)

| Scratch training source | Selected update | CIC test | UNSW test |
| --- | --- | --- | --- |
| CIC only | 100 | 50.00% | 50.00% |
| UNSW only | 100 | 50.00% | 50.00% |
| Joint | 1,000 | 55.57% | 50.00% |

Test scores are group weighted balanced accuracy.

### 00:38:22 — Nine simple controls challenge neural superiority

Nine controls help interpret the neural results. Each source choice uses three methods: a majority classifier, which always predicts the class with more weighted training group target mass; a histogram model, which counts byte frequencies; and a metadata model, which uses recorded properties. Metadata stays outside the neural model's inputs. The U N S W only metadata control reaches ninety-nine point thirty-four percent group balanced accuracy. It exceeds every native model tested on that source. These recorded properties strongly distinguish this source's labels. The methods use different inputs, and their results do not establish that neural models are uniformly superior.

On screen: 3 source choices × majority, histogram, and metadata · UNSW metadata: 99.34% group balanced accuracy there · Different input features are part of the comparison

Evidence: [packet-controls](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/controls/evaluation/results.json), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md)

### 00:39:08 — Class agreement and numerical agreement are distinct

The original full inference check reproduced every class across twenty five thousand nine hundred thirty predictions, while two rows failed the strict logit comparison. A separate fresh client run validated twenty thousand C I C rows and predicted one hundred twenty eight. All those classes agreed, but seventy six rows failed the strict numerical comparison. Both checks used relative tolerance one ten thousandth and absolute tolerance one millionth. A tolerance defines the allowed numerical difference. The fresh maximum difference is preserved exactly on screen. Agreement on a class does not make the underlying scores numerically identical.

On screen: Original full check and fresh capped check remain separate · Failures count compared prediction rows

Evidence: [packet-results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/results.json), [client-audit](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/research/packet-checks/client-export.json), [packet-prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/predict_packets.py), [prediction-agreement](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/unlabeled/agreement.json)

| Check scope | Validated / predicted | Classes agree | Strict logit failures |
| --- | --- | --- | --- |
| Original full check | 25,930 / 25,930 | 25,930 | 2 rows |
| Fresh client check | 20,000 / 128 | 128 | 76 rows |

Fresh max |Δlogit| = 0.006159305572509766; rtol=1e-4, atol=1e-6.

### 00:39:51 — State what the evidence still cannot establish

Report these results with the conditions that make them interpretable. The study used one model seed, capped training pools, and a fixed update budget. The earlier data seen by the released pretrained weights is unknown. Exact payload grouping also cannot prove independence between network captures. The selected C I C test has no PortScan rows and only four distributed denial of service rows, so broad subtype claims would exceed its support. Finally, the paper's ninety seven point five zero percent flow accuracy measures a different task and metric. These packet results establish neither its reproduction nor an improvement over it.

On screen: One model seed, capped pools, fixed update budget · Earlier pretrained exposure remains unknown · CIC test: 0 PortScan rows; only 4 DDoS rows

Evidence: [packet-protocol](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/protocol.json), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [packet-results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/results.json)

### 00:40:34 — Your turn · 10 seconds

**Practice pause: 10 seconds.** State one measured success, one weak result, and two remaining limits.

On screen: State one measured success, one weak result, and two remaining limits.

Evidence: [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [packet-results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/results.json), [client-audit](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/research/packet-checks/client-export.json)

## 00:40:44 — Show the packet demo and explain a mistake

### 00:40:44 — Start with the right demonstration

Now demonstrate the system to someone else. Open the packet viewer from the project home page, or generate the same page from the client repository. The viewer displays predictions already produced by the selected joint model. It does not train a model or inspect your current network. Say that boundary before clicking anything. This makes the demonstration useful: you can show real model decisions and their limitations without pretending a browser is an operational security system. The next steps follow the same saved packet evidence used in the results chapter.

On screen: Recorded joint-model predictions · Both packet sources · No live network connection

Evidence: [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [packet-demo](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/render_packet_demo.py)

### 00:41:18 — Choose the source you are explaining

The source selector switches between the C I C and U N S W test groups. The C I C view contains twenty thousand distinct payload groups; the U N S W view contains five thousand nine hundred thirty. These are selected test groups, not the original total CSV row counts. The headline cards always describe the complete selected source test set. Table filters only choose which saved rows appear on screen. Explain which source is selected before reading any metric, because the model performs differently on the two sources.

On screen: CIC: 20,000 test groups · UNSW: 5,930 test groups · Headline metrics use the complete source

Evidence: [packet-demo](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/render_packet_demo.py), [packet-results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/results.json), [packet-capture](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/demo/video/v5/recordings/capture.json)

### 00:41:53 — One decision has several parts

Open one prediction's detail panel. The long hash identifies the exact payload group without displaying the original bytes. The model produced two logits, which are numerical scores before conversion into probabilities. The larger logit chooses benign or attack. The viewer also shows an uncalibrated probability for that choice. A large value means the model favors one class under its learned scoring rule. It does not prove that the packet is dangerous, and it is not a measured probability that an analyst will confirm an attack on a customer network.

On screen: Payload hash identifies the byte group · Two logits determine the class · Scores are uncalibrated

Evidence: [packet-demo](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/render_packet_demo.py), [packet-prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/predict_packets.py)

### 00:42:31 — Keep the supplied labels visible

The same payload can appear in multiple rows with different supplied labels. The viewer therefore keeps the benign and attack row counts for each group. It does not silently choose a convenient single label. For example, a hypothetical group with nine benign labels and one attack label still contains both kinds of evidence. A benign prediction disagrees with the one attack-labeled row. That example explains the interface; it is not an additional measured result. The original labels have not been independently adjudicated, so disagreements can reveal model errors, label problems, or both.

On screen: Original benign and attack row counts · Conflicting labels remain visible · A group is not automatically one true label

Evidence: [packet-demo](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/render_packet_demo.py), [packet-data](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_data.py)

### 00:43:10 — Demonstrate an error without hiding it

Select the disagreement filter and inspect a result. The point is to show how a model can be wrong, including when its own score is high. Read the predicted class and the original label counts together. If you choose the conflicting-label filter, explain why disagreement is unavoidable for some rows sharing identical model inputs. Do not call every displayed disagreement a proven malicious packet that was missed. This is a labeled research dataset with a specific evaluation rule. A credible presentation explains that rule and shows an actual limitation alongside the positive results.

On screen: Actual saved error: Attack, 94.57% uncalibrated score · Supplied labels: 1 benign, 0 attack · A prediction is not an independently verified incident

Evidence: [packet-demo](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/render_packet_demo.py), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [packet-capture](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/demo/video/v5/recordings/capture.json)

### 00:43:50 — Fresh prediction is a separate execution step

Fresh inference happens in the Python packet predictor using the checked GPU environment and a trained joint checkpoint. It accepts a correctly formatted unlabeled CSV and writes predictions plus a receipt. The label column must be removed in a separate input copy because inference must not receive the answers. The new receipt distinguishes validated rows from predicted rows when a prediction cap is used. Opening the viewer and running the predictor demonstrate different parts of this workflow. The viewer explains retained results; the predictor performs a new model computation.

On screen: Supply an unlabeled packet CSV · Load the selected joint checkpoint · Retain predictions and the receipt

Evidence: [packet-prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/predict_packets.py), [client-setup](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/client/SETUP.md.in), [client-audit](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/research/packet-checks/client-export.json)

### 00:44:29 — What a working IDS would add

An operational intrusion detection system would connect additional components around this classifier. It would capture traffic, extract bytes with the same meaning as the training inputs, queue examples, run inference, apply a reviewed alert policy, and store events for investigation. Monitoring would need to report dropped packets and processing failures. A blocking system would need further response and recovery decisions. None of those components appears merely because a prediction says attack. The working demonstration here is a recorded packet viewer plus an actual CSV inference program. The missing operational components remain explicit engineering work.

On screen: Capture and compatible byte extraction · Inference queues and alert policy · Monitoring, review and response

Evidence: [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [hardware](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/hardware-roadmap.md)

### 00:45:12 — Your turn: explain it aloud

**Practice pause: 10 seconds.** Explain what the browser demonstrates and what requires the GPU predictor.

On screen: Explain what the browser demonstrates and what requires the GPU predictor.

Evidence: [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md)

## 00:45:22 — Set up, run and test the same packet workflow

### 00:45:22 — Start from the client repository

For a person who needs to run the delivered project, start from the client repository. Clone it, enter its root directory, and read the setup document there. The source repository remains useful for development and the longer explanations, but the client contains the selected execution files and their tests. Use a new output directory for each experiment. That preserves the previous run, its errors, and its identity records.

On screen: Clone netmambaplus-client · Read SETUP.md from its root · Keep output directories separate

Evidence: [client-setup](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/client/SETUP.md.in), [client-readme](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/client/README.md.in)

```text
git clone https://github.com/buffbeefalo/netmambaplus-client.git
cd netmambaplus-client
python -m unittest discover -s tests -v
python tools/verify_client.py
```

### 00:45:50 — Check the portable parts first

The first commands need Git and a supported Python interpreter, without a GPU or the private CSV files. Run the tests, verify the delivered inventory and evidence, and generate the packet viewer. On the recorded local Linux check, the client discovered one hundred eighty-five tests. One hundred forty-nine passed and thirty-six optional tests skipped. A skip is not a successful native GPU test. Windows had one additional skip in its hosted jobs. These counts belong to the recorded delivery revision. Later software revisions can change the suite, so retain the run output.

On screen: Python 3.10 or 3.12 · Tests and saved-evidence verification · Offline packet viewer

Evidence: [client-audit](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/research/packet-checks/client-export.json), [client-setup](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/client/SETUP.md.in)

```text
python -m unittest discover -s tests -v
python tools/verify_client.py
python tools/render_packet_demo.py \
  --output runs/packet-demo-new
```

### 00:46:28 — Prepare the native execution environment

Actual neural execution needs more than the portable test suite. The measured environment used Linux on A R M sixty-four, an NVIDIA G B ten, Python three point twelve, and Torch two point nine point one with CUDA thirteen. The compiler toolkit and custom operators also matter. A driver displaying a CUDA version does not mean the compiler is installed. Follow the exact package and environment commands in the setup document. Other physical GPUs need their own build, numerical and packet-model checks. Hosted Windows and macOS checks do not prove native neural execution there.

On screen: Measured: Linux ARM64 and GB10 · Torch plus CUDA toolkit and custom operators · Other GPUs need their own checks

Evidence: [client-setup](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/client/SETUP.md.in), [support](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/support-matrix.md), [native-gate](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/research/packet-checks/native-receipt.json)

### 00:47:07 — Acquire only the required initialization

The setup obtains the pinned authors' source and checks its identity. The default asset fetch now acquires only the registered pretrained initialization, with its expected size and hash. It does not download a flow dataset. It also does not supply your two private CSVs or a finished binary packet classifier. You provide the CSVs locally and training produces the selected packet checkpoint. This explains why cloning the repository is enough to inspect evidence but not enough to run a trained application immediately. The asset notice records attribution and unresolved inherited terms.

On screen: Verify the pinned authors’ source · Fetch pretrained weights separately · Supply both CSVs locally

Evidence: [client-setup](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/client/SETUP.md.in), [packet-assets](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/configs/assets.json), [client-notice](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/client/NOTICE.md.in)

```text
python repro.py fetch
python tools/fetch_assets.py --output assets
python tools/build_cuda.py \
  --build-root runs/cuda-build-new
python tools/check_gpu_runtime.py \
  --output runs/cuda-ops-new.json
```

### 00:47:48 — Prepare both inputs and run the native gate

Run packet preparation with both input paths and a fresh destination. It validates every row and byte, creates the global groups and partitions, and saves arrays with a manifest. For an exact repeat of the uploaded-file study, check the registered source identities in that manifest. The packet runtime gate then uses prepared bytes from both sources to exercise transfer, input shapes, gradients, an optimizer update and checkpoint reload. All seventeen cases passed on the recorded G B ten checks. The loss targets in that gate are synthetic, so its pass is functional evidence, not benchmark accuracy.

On screen: Validate and group both CSVs · Check registered source identities · Require native tests with no skips

Evidence: [client-setup](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/client/SETUP.md.in), [native-gate](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/research/packet-checks/native-receipt.json), [packet-data](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_data.py)

### 00:48:28 — Freeze, train, select and predict

The setup gives the full commands to freeze a protocol, fit the controls, train the six comparison arms and evaluate the frozen results. Protocol freezing binds the data, implementation and declared budget. Read the completed receipts rather than assuming a requested number of updates finished. The selected joint pretrained checkpoint is listed in the frozen checkpoint file. Use that path for the client's prediction command. It belongs to this same packet workflow; the other arms are comparisons that help explain the chosen model. Preserve any failure report while investigating a new run.

On screen: Freeze the protocol before the study · Complete the six comparison arms · Use the joint pretrained checkpoint

Evidence: [client-setup](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/client/SETUP.md.in), [packet-protocol](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/packet-study/protocol.json), [packet-training](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/train_packet_model.py), [packet-prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/tools/predict_packets.py)

### 00:49:07 — Read a failed check before retrying

If a check fails, identify whether the failure concerns input format, source identity, a missing operator, incomplete execution, or numerical agreement. Those are different problems with different fixes. Keep the failed report and use a new output path for a corrected execution. Do not loosen a scientific tolerance just to make a presentation green. The current record deliberately retains score-comparison failures even when predicted classes match. That makes the project more useful to the next engineer, who can see what was tested, what succeeded, and which remaining issue still requires investigation.

On screen: Find the failing stage and receipt · Correct the cause in a new run · Never turn a skip into a pass

Evidence: [client-setup](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/client/SETUP.md.in), [client-audit](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/research/packet-checks/client-export.json), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md)

### 00:49:47 — Your turn: explain it aloud

**Practice pause: 10 seconds.** Name the evidence needed before claiming a new machine runs the native model.

On screen: Name the evidence needed before claiming a new machine runs the native model.

Evidence: [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md)

## 00:49:57 — Understand both repositories and their updates

### 00:49:57 — Two repos, one packet application

There are two repositories because their audiences need different amounts of material. The reproduction repository is the development and research source. It includes the full explanations, historical work, presentation builders and teaching materials. The client repository is a concise executable delivery with the packet code, selected dependencies, tests and evidence. They do not offer competing model workflows. Both lead to the same joint packet adaptation using the two CSVs. Tell a presenter to begin with the reproduction guide, and tell the engineer receiving the executable handoff to begin with the client setup.

On screen: Reproduction: develop, investigate and learn · Client: run the concise delivery · Shared code follows one workflow

Evidence: [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [client-readme](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/client/README.md.in), [client-maintenance](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/research/client-edition.md)

### 00:50:37 — The model and data files have distinct jobs

The top-level packet data module validates inputs, maps labels, groups identical payloads and constructs prepared artifacts. The packet model module connects the supplied bytes to the original encoder, handles compatible pretrained transfer and defines the binary classifier. The packet study module supplies shared experiment and evidence functions. Keeping those responsibilities distinct makes the project easier to check. If an input row is rejected, investigate preparation or inference parsing. If checkpoint shapes disagree, investigate the model contract.

On screen: packet_data.py prepares inputs · packet_model.py adapts the encoder · packet_study.py supports the experiment

Evidence: [packet-data](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_data.py), [packet-model](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_model.py), [packet-study](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_study.py)

### 00:51:16 — Tools, configs and requirements support execution

The tools directory contains the programs for source and asset acquisition, native builds, runtime checks, protocol freezing, controls, training, prediction, evidence review and demo rendering. Configurations record settings and asset identities. Requirements record the measured dependency set. The shared reproduction helper remains an internal dependency for upstream identity and build operations, even in the client. Its historical orchestration does not create another supported client workflow. Use the documented packet setup rather than exploring old commands as if they were additional product choices. Each tool should have an identifiable input, output and checkable completion condition.

On screen: Tools run specific workflow stages · Configs record settings and identities · Requirements define the measured environment

Evidence: [client-setup](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/client/SETUP.md.in), [client-maintenance](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/research/client-edition.md), [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md)

### 00:52:03 — Evidence and local runs are different objects

The public evidence directories contain saved predictions, metrics, protocols, receipts and hashes that support the published claims. Local run directories contain machine-specific execution outputs and separately acquired assets. Raw CSVs, the authors' checkout and trained weights are not automatically part of a public source clone. In the full reproduction repository, older flow experiments and calibration records remain historical research. They help explain earlier work but are not the present client setup. The file walkthrough explains individual paths and downloads so you can tell an executable component from a result, a source document or a generated artifact.

On screen: Public receipts and saved predictions · Local CSVs, prepared arrays and weights · Historical research stays labeled

Evidence: [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [client-notice](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/client/NOTICE.md.in), [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md)

### 00:52:46 — The client manifest identifies the delivery

At the recorded packet-only delivery, the client contained one hundred twenty-four files, including its manifest. Seventy-five were packet-study evidence files. The manifest records the selected source revision, the origin of each delivered file, its size and its hash. A hash answers whether the bytes match a recorded identity. It does not prove that the scientific claim is true. The evidence reviewer adds arithmetic and consistency checks. Together these mechanisms let the recipient establish which software and results they received, while still reading the limits of the actual experiment.

On screen: 124 files at the recorded delivery · 75 packet-study evidence files · Exact source paths and SHA-256 hashes

Evidence: [client-maintenance](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/research/client-edition.md), [client-audit](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/research/packet-checks/client-export.json)

### 00:53:25 — Updates flow from source to client

Development changes belong in the reproduction repository, including the templates used to generate client instructions. After successful source checks, the publication workflow selects the tested source revision and builds an explicit client export. It rejects unexpected client edits and checks the staged contents before publication. A separate publishing step updates the client, whose own platform checks then run. The packet-only update actually exercised managed removal of older flow files. If you manually change the client and it diverges, synchronization stops for review instead of silently overwriting the difference. This protects the handoff's identity.

On screen: Successful source CI gates publication · Export checks additions and removals · Client CI checks the delivered revision

Evidence: [client-maintenance](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/research/client-edition.md), [client-audit](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/research/packet-checks/client-export.json)

Reproduction: Develop code + templates
Checks / export: Test selected source
Client: Publish shared workflow
Source updates produce a verified client export; teaching media stays in reproduction.

### 00:54:08 — Find the right download and its scope

This video, its captions, transcript, slide deck and handbook come from one reviewed lesson source. Their records bind the rendered assets to that source. The handbook includes the repository file guide for details that would be tedious to read aloud. The shorter packet presentation remains a concise summary of the same study. Teaching media belongs in the reproduction repository and is excluded from the client export. An explanation-only source edit may therefore leave the client's source marker unchanged. A selected code or template change follows the verified update process described in the previous scene.

On screen: Video, captions and transcript share a source · Slides and handbook follow the lesson · Client excludes teaching media

Evidence: [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [client-maintenance](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/research/client-edition.md), [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md)

### 00:54:47 — Your turn: explain it aloud

**Practice pause: 10 seconds.** Explain which repo you would give a presenter and which you would give an engineer.

On screen: Explain which repo you would give a presenter and which you would give an engineer.

Evidence: [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md)

## 00:54:57 — Hardware roadmap, remaining work and your handoff

### 00:54:57 — Start with the complete processing path

Now consider a future deployment. Draw the entire path from observed network traffic to a usable security event. Capturing bytes, identifying the correct representation, buffering work, transferring data, running the classifier and recording an alert all take time and can fail. A model-only timing would not include those stages. This packet handoff does not establish operational throughput, end-to-end latency or an alert guarantee. The first hardware task is to define that complete path and its requirements. Only then can an engineering team decide which stages should run on which device.

On screen: Capture and extract compatible bytes · Queue, infer and produce an event · Measure the whole path

Evidence: [hardware](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/hardware-roadmap.md), [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md)

### 00:55:35 — What a SmartNIC could contribute

A network interface card moves network data into and out of a system. A Smart N I C adds programmable processing near that network boundary. It could contribute capture, filtering, buffering or compatible preprocessing, depending on the specific hardware and runtime. Those are proposed responsibilities, not capabilities demonstrated by this repository. In particular, putting a model file on a network card does not establish correct packet extraction or reliable inference. The representation must match the packet bytes the model expects, and the complete system must report overload, dropped observations and processing failures.

On screen: Network-facing capture and buffering · Possible preprocessing and queue handling · No completed target deployment

Evidence: [hardware](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/hardware-roadmap.md), [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md)

### 00:56:17 — What an NPU port would require

A neural processing unit accelerates computations supported by its own runtime. Net Mamba Plus currently relies on custom CUDA operations in the checked native implementation. A future port needs a chosen target, supported equivalents for the relevant operations, compatible layouts and an explicit precision policy. Saving parameter tensors is different from exporting an executable computation graph. Both may be necessary, and neither alone proves the port works. Begin by comparing the target's model outputs with the retained GPU reference. Preserve differences and determine whether they change decisions under the intended operating conditions.

On screen: A target runtime and supported operators · Equivalent tensor layouts and precision · Compare outputs against the GPU reference

Evidence: [hardware](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/hardware-roadmap.md), [packet-model](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/packet_model.py), [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md)

### 00:56:59 — Optimization needs a new measurement plan

Optimizations should answer a stated deployment need. Larger batches may improve throughput while increasing how long a packet waits. Lower precision can save memory or computation while changing scores and possibly classifications. Faster arithmetic does not automatically make the detector more useful. A target evaluation should include accuracy on suitable data, latency distributions, throughput, memory use and dropped work. The existing strict score-comparison failures already show why class agreement and identical numerical outputs must be reported separately. A port needs its own evidence instead of borrowing a successful check from another machine.

On screen: Batching changes latency and throughput · Lower precision can change predictions · Compare accuracy, failures and resource use

Evidence: [hardware](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/hardware-roadmap.md), [client-audit](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/research/packet-checks/client-export.json), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md)

### 00:57:44 — The major research gaps remain visible

The current results come from one model seed, capped groups and these supplied data sources. Pretrained exposure to related data is not fully known. Exact duplicate grouping does not prove independent captures, and sparse attack-subtype support limits some conclusions. The project has not established reliable confidence on customer traffic, calibrated packet probabilities, unknown-attack coverage, operational alert thresholds or live capture. It also has not run on an N P U or Smart N I C. These are concrete next tests and engineering tasks. They do not erase the completed training, but they constrain what it proves.

On screen: Independent customer traffic and more seeds · Unknown attacks and reliable confidence · Live extraction, alerts and target execution

Evidence: [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [hardware](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/hardware-roadmap.md), [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md)

### 00:58:25 — Say precisely what has been built

Here is a defensible explanation. We adapted the original Net Mamba Plus encoder to packet payloads from both supplied CSV files. We validated the inputs, grouped exact duplicate payloads across sources, trained the declared comparison models and selected checkpoints using validation data. We measured the joint model on held-out packet groups and compared it with simpler controls. We executed saved-checkpoint inference and retained both class agreement and numerical differences. The client repository delivers the executable workflow; the reproduction repository explains the code, evidence and limitations. This is a tested research implementation, with further work required for deployment.

On screen: Both CSVs really enter native training · The joint classifier predicts packet labels · The records include weak results and failures

Evidence: [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [client-audit](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/research/packet-checks/client-export.json)

### 00:59:10 — Teach the complete story to the next person

For your final handoff, explain the project without reading a list of filenames. Begin with the two CSVs and the paper's idea. Follow one packet through preparation, the adapted encoder, training and inference. State what the joint results measure and mention the stronger metadata control on U N S W. Explain what each repository is for and where to find the setup and audit. Finish with the difference between the recorded demonstration and an operational intrusion detector. Take the upcoming pause to practice that story aloud. Use the transcript afterward to check anything you could not explain clearly.

On screen: Inputs, model, training and predictions · Both repos, tests and measured results · Limits and the next deployment experiment

Evidence: [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md), [packet-report](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/packet-model-study.md), [client-maintenance](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/research/client-edition.md)

### 00:59:50 — Your turn: explain it aloud

**Practice pause: 10 seconds.** Explain the complete CSV workflow, both repos, one measured result and one remaining limitation.

On screen: Explain the complete CSV workflow, both repos, one measured result and one remaining limitation.

Evidence: [project-guide](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/client-project-guide.md)
