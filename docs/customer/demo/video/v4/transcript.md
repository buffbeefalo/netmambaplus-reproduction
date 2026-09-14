# NetMamba+ — understand the complete repository — transcript

Synthetic narration rendered from reviewed text. This video explains recorded experiments; it does not perform new training or live capture.

Runtime: 01:00:00, including 03:20 of labeled practice pauses. Caption timing: Speech-service word boundaries mapped through the final audio timing; independent encoded-audio checks are reported separately. Full human listening and caption-alignment review remain pending.

Author: Codex · Director: Codex · Narration role: Microsoft Andrew neural voice renders Codex-authored text through edge-tts; it does not author the lesson. · Text authorship: Codex authored the lesson; no local language model wrote the narration. · Human full watch: not performed; automated audits are reported separately

## 00:00:00 — Start here: what you built

### 00:00:00 — A research lab you can explain

Welcome. This course will take you from the three files you started with to a clear explanation of the repository you now have. You do not need a networking or machine learning background. We will read the paper's ideas, inspect both spreadsheet shaped datasets, follow a flow through the original model, and examine the experiments that actually ran. Then we will walk through the code, setup, tests, downloads, demonstration, and hardware roadmap. Codex wrote and produced this lesson. A synthetic voice renders the narration. The research claims come from recorded evidence.

On screen: Paper → research proposal · Repository → executable experiment · Evidence → what actually happened

Evidence: [answers](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/answers.md), [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md), [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md)

### 00:00:36 — The result to remember

The central result is a working, measured reproduction attempt. The original multimodal classifier trained and performed inference on compatible research flows using an NVIDIA G B ten graphics processor. Three full fine tuning runs achieved an average test accuracy of eighty six point six five percent. The paper reports ninety seven point five percent for its comparison. We did not reproduce that number. We also did not build a complete live intrusion detection system. Those limits do not erase the work. They tell you precisely what the work establishes and what a next experiment needs to resolve.

On screen: Three full fine-tuning runs on compatible flows · Mean test accuracy: 86.65% · Paper result: 97.50% — not reproduced

Evidence: [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json), [verification](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/verification.md)

### 00:01:17 — Packet, header and payload

A network moves information in packets. Think of one packet as a small delivery envelope. Its header contains information used to handle the delivery. Its payload contains the carried content, which may be encrypted. A byte is a small numerical unit with values from zero to two hundred fifty five. The model can process those numbers without turning them into readable sentences. The envelope analogy is only a starting point: real packets use several protocol layers, and a payload is not guaranteed to contain a complete application message. One conversation usually spans many packets.

On screen: Packet: a small unit sent across a network · Header: delivery and protocol information · Payload: carried content, possibly encrypted

Evidence: [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md), [lesson](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/lesson.md)

### 00:01:55 — A flow needs a grouping rule

A flow is a set of related packets, grouped using an explicit rule. A common starting point uses source and destination addresses, source and destination ports, and the transport protocol. Direction handling, timeouts, and packet ordering also need a definition. Imagine two cameras sending messages at the same time. The next two captured packets could belong to different cameras. Their proximity in a file does not make them one conversation. This matters because Net Mamba Plus learns from a structured view of a flow. Supplying unrelated packet rows changes the meaning of its input.

On screen: Related packets must be grouped · Their order and timing matter · Adjacent CSV rows do not prove a connection

Evidence: [csv](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/uploaded-csv-profile.json), [native](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/native-data-validation.json), [contract](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/harness-reference.md)

### 00:02:34 — Classifier, detector and response

An intrusion detection system, often shortened to I D S, observes traffic and raises alerts for investigation. The neural classifier is one component that can help assign a category. Capture, flow assembly, data transformation, alert thresholds, event storage, and operational response are additional components. A prediction alone does not decide whether to block a customer connection. In this project the browser demonstration displays previously recorded predictions. That is useful for explaining behavior and mistakes, but opening the page does not connect to a network tap or execute a model inside your browser.

On screen: Classifier: select a category · IDS: observe traffic and manage alerts · Response: investigate or enforce a policy

Evidence: [answers](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/answers.md), [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md), [prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/seed0/replay/predictions.json)

### 00:03:14 — How to read an evidence claim

Throughout the lesson, separate three claims. Implemented means there is code intended to do a job. Executed means a recorded command actually ran. Validated means a specific check passed against a stated expectation. A script can exist without its hardware path being tested. A training job can complete without matching a published accuracy. A checksum can match without proving the dataset is unbiased. When someone says everything works, ask which activity, on which environment, with which evidence. The repository's manifests, logs, predictions, and failure records make that question answerable.

On screen: Implemented: code exists · Executed: a recorded command ran · Validated: a named check passed

Evidence: [verification](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/verification.md), [support](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/support-matrix.md), [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md)

### 00:03:54 — Your presentation has an evidence trail

You now have the vocabulary needed for the rest of the course. We will use short questions to check understanding, with clearly labeled pauses that resume automatically. The transcript repeats the narration and links each scene to supporting files. The companion file guide explains every tracked file and every release download, so you can look up a particular filename without memorizing the directory tree. First, practice the most important boundary. Does a working classifier prove that a complete live security system has been deployed? Take ten seconds to formulate your answer.

On screen: Watch this course to learn the story · Use the transcript to explain it again · Use the file guide to find each underlying record

Evidence: [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md), [answers](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/answers.md)

### 00:04:31 — Your turn · 10 seconds

**Practice pause: 10 seconds.** Does a working classifier prove a complete live IDS?

On screen: Does a working classifier prove a complete live IDS?

Evidence: [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md), [answers](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/answers.md)

## 00:04:41 — The PDF: ideas, experiments and boundaries

### 00:04:41 — What the attached PDF is

The answer is no: the classifier is one tested component. Now open the attached paper conceptually. It is the January twenty twenty six first preprint version of Net Mamba Plus, a framework of pretrained models for efficient and accurate network traffic classification. A research paper describes a problem, a proposed method, experiments, and conclusions. It is not an installation manual or a complete specification of every released data file. This paper covers several model variants and datasets. Our repository exercises a particular multimodal Mamba classifier and one compatible downstream dataset, so its scope is narrower.

On screen: arXiv 2601.21792v1 · January 2026 · Traffic classification research · A framework with more than one model variant

Evidence: [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md), [paper-notes](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/paper-and-data-explained.md)

### 00:05:23 — Three problems motivate the paper

The authors identify three difficulties. First, some sequence models become expensive when processing many input units. Second, a traffic representation may discard useful content while keeping misleading clues, such as identifiers tied to the collection environment. Third, common categories can dominate learning while rare categories perform poorly. These are distinct problems. A faster model does not automatically fix biased input data. Adding packet timing does not automatically solve a rare class problem. The paper combines architectural, representation, and training ideas to address them. Our measurements should be interpreted against the parts actually enabled.

On screen: Computation cost of long sequences · Information lost or biased during extraction · Rare categories hidden by class imbalance

Evidence: [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md), [paper-notes](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/paper-and-data-explained.md)

### 00:06:10 — What multimodal means here

Multimodal means using several views of the same observation. Here it means packet byte content, packet lengths, and time gaps. Suppose two flows contain similarly encrypted bytes, but one sends a steady series of small packets while another sends large bursts. Size and timing can provide additional structure. This is an explanatory example, not a measured claim about our test set. The important requirement is that all three views describe the same flow. Combining bytes from one connection with timing from another would create a physically inconsistent example even if the tensor dimensions still matched.

On screen: Bytes: content patterns · Sizes: transmission shape · Intervals: transmission rhythm

Evidence: [lesson](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/lesson.md), [config](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/configs/ciciot2022.json)

### 00:06:49 — Mamba and the alternative backbone

The paper discusses Mamba and an alternative optimized Transformer called Net Trans. Flash Attention belongs to that alternative's attention implementation; it is not evidence that our active Mamba classifier uses an attention layer. A Mamba block processes a sequence while updating numerical state, with updates influenced by the input. This can make sequence processing efficient. It does not mean the software maintains a live table of network connections between predictions. In our tested configuration the classifier uses four Mamba blocks. Other branches present in a source repository are not automatically exercised by that configuration.

On screen: Mamba: input-dependent state updates · NetTrans: a separate attention-based alternative · Our run uses the Mamba classifier

Evidence: [paper-notes](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/paper-and-data-explained.md), [lesson](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/lesson.md), [config](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/configs/ciciot2022.json)

### 00:07:30 — Read the paper in this order

For a first reading, use the framework diagram to understand the overall path. Then read the traffic representation section to see how raw traffic becomes structured inputs. The model details explain embeddings, sequence processing, pretraining, and classification. The online system section adds capture and shared memory around a classifier. The evaluation section reports dataset comparisons, efficiency, and other experiments. Keep a note beside each number identifying the model, task, and machine that produced it. This reading habit prevents a result from one experiment being accidentally used as proof for a different system.

On screen: Framework and representation: sections IV–V · Model and learning details: section VI · System and measurements: sections VII–VIII

Evidence: [paper-notes](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/paper-and-data-explained.md), [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md)

### 00:08:12 — A table is not our result

The paper's comparison includes a ninety seven point five percent accuracy figure for the relevant C I C IoT twenty twenty two result. Our three seed mean is eighty six point six five percent. We preserve both numbers and the differences in runtime and training settings. We did not isolate the cause of the gap. The paper also studies few shot learning, unfamiliar distributions, and a label distribution aware strategy for imbalanced classes. Those results do not become reproduced merely because our basic classifier runs. Each additional claim would need its own matching protocol, inputs, and measured outputs.

On screen: Paper Table IV: 97.50% for CICIoT2022 · Paper also studies other tasks and settings · Our three-run mean: 86.65%

Evidence: [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json), [paper-notes](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/paper-and-data-explained.md)

### 00:08:54 — Two details that prevent overclaiming

Two details deserve special care. A token is a numerical input unit for the sequence model; we will build those units later. The paper's hyperparameter table shows four hundred one tokens for its byte representation. Our actual multimodal classifier receives four hundred forty three tokens, after including sizes, intervals, and three summary tokens. Later, the paper reports online throughput of two hundred sixty one point eight seven megabits per second for its Net Mamba prototype on different hardware. That is not our measured multimodal deployment. Before presenting any paper number, identify the exact experiment it describes. Take ten seconds to name one paper claim that this repository has not independently reproduced.

On screen: Paper byte sequence: 401 tokens · Our multimodal sequence: 443 tokens · Paper online throughput is a separate NetMamba prototype

Evidence: [paper-notes](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/paper-and-data-explained.md), [lesson](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/lesson.md), [hardware](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/hardware-roadmap.md)

### 00:09:45 — Your turn · 10 seconds

**Practice pause: 10 seconds.** Name one paper claim that has not been reproduced here.

On screen: Name one paper claim that has not been reproduced here.

Evidence: [paper-notes](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/paper-and-data-explained.md), [lesson](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/lesson.md), [hardware](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/hardware-roadmap.md)

## 00:09:55 — The first CSV: CICIDS2017 packet records

### 00:09:55 — A CSV is a table, not a running database

Examples include the paper's headline accuracy, its full pretraining protocol, and its online throughput. Next, inspect your first attached data file. A C S V is plain text organized as rows and comma separated fields. A spreadsheet can display it as a table, but this file is not a database server or a network capture program. The full profile counted one million four hundred ten thousand two hundred fifty five packet records in the C I C I D S twenty seventeen file. Each row has fifteen hundred five columns. The stored profile lets you inspect that structure without opening a multi gigabyte spreadsheet.

On screen: Rows: individual records · Columns: named fields · This file: 1,410,255 rows and 1,505 columns

Evidence: [csv](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/uploaded-csv-profile.json), [paper-notes](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/paper-and-data-explained.md)

### 00:10:35 — One row contains five kinds of metadata

Fifteen hundred columns are named payload byte one through payload byte fifteen hundred, using underscores in the exact header names. They describe payload byte positions. Five additional columns are time to live, total length, protocol, a delta time field, and the label. Time to live is a protocol field limiting how far a packet can travel; it is not a timestamp. Total length is a recorded packet length value. Protocol describes the communication protocol. Delta time suggests a time difference, but the CSV alone does not establish its units or how it was computed. The label is the category supplied with the record.

On screen: payload_byte_1 … payload_byte_1500 · ttl / total_len / protocol / t_delta · label: the recorded category

Evidence: [csv](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/uploaded-csv-profile.json)

### 00:11:16 — Benign and attack labels are imbalanced

This CSV contains fifteen label names. The largest group is labeled benign, with three hundred sixty two thousand one hundred eight rows. Do S Hulk has two hundred fifty thousand, and D Do S has two hundred forty one thousand four hundred five. In general terms, a denial of service attack attempts to disrupt availability, and a distributed denial of service uses multiple sources. Here those are dataset labels, not events newly detected by our model. The table also contains credential attack, web attack, scanning, bot, infiltration, and other categories. Their counts describe this supplied extract, not every version of the original dataset.

On screen: BENIGN: 362,108 rows · DoS Hulk: 250,000 rows · DDoS: 241,405 rows

Evidence: [csv](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/uploaded-csv-profile.json)

### 00:12:00 — Why the small classes matter

At the small end, Port Scan has eight hundred thirty rows. The web attack SQL injection label has only twelve. That is why a single overall accuracy can hide a serious weakness. Imagine a model that handles a common label well but fails every rare example. Its aggregate score might still look impressive. A defensible packet classifier study would examine per class support, precision, recall, and a confusion matrix, with careful splitting. We have not trained that packet classifier here. These counts explain a possible future adaptation and its evaluation requirements; they do not report new model performance.

On screen: PortScan: 830 rows · Web Attack – Sql Injection: 12 rows · A good overall score can hide rare-class failures

Evidence: [csv](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/uploaded-csv-profile.json)

### 00:12:40 — Odd values are questions to investigate

The full metadata scan also found negative delta times, with a minimum of negative zero point zero zero zero zero one eight. We do not know the time unit from this extract. Some recorded total lengths exceed fifteen hundred even though there are fifteen hundred payload columns. Those observations are reasons to investigate the extraction procedure. They are not enough to diagnose corruption, reconstruct missing headers, or invent time ordering. A field name is a clue, not a complete data contract. Our strict native flow path requires observed intervals to be finite and nonnegative, so blindly copying these values would be unsafe scientifically.

On screen: Some t_delta values are negative · Minimum observed: −0.000018 · Some total_len values exceed 1,500

Evidence: [csv](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/uploaded-csv-profile.json), [contract](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/harness-reference.md)

### 00:13:23 — What the profiling actually checked

The profiling program scans the full file to count rows and aggregate the selected metadata. That is stronger evidence than looking at the first fifty rows. However, it is narrower than exhaustively validating every payload byte cell. The report states that limit explicitly. It records file size and a content hash so another person can identify the same input. It does not recover capture history, packet direction, or a flow identifier that the columns do not supply. Keeping the exact scope of a data audit visible prevents a useful profile from being mistaken for a complete certification.

On screen: Full-file row counts and metadata aggregates · Label and protocol distributions · Payload values were not exhaustively validated

Evidence: [csv](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/uploaded-csv-profile.json), [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md)

### 00:14:03 — The missing information changes the task

Most importantly, the supplied schema does not establish source and destination addresses, ports, a flow identifier, or packet order within a flow. Its payload byte columns also do not establish the paper's header and payload representation. Taking five neighboring rows and calling them one flow would add an unsupported assumption. A classifier trained directly on these rows could still be an interesting project, but it would be a packet based adaptation with its own labels and evaluation. Take ten seconds: explain why matching the number of numeric columns would not make these rows compatible Net Mamba Plus inputs.

On screen: No established addresses, ports or flow ID · No established order within each flow · Payload-only rows cannot establish header semantics

Evidence: [csv](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/uploaded-csv-profile.json), [contract](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/harness-reference.md)

### 00:14:43 — Your turn · 10 seconds

**Practice pause: 10 seconds.** Why is matching a tensor shape insufficient to establish compatible flow data?

On screen: Why is matching a tensor shape insufficient to establish compatible flow data?

Evidence: [csv](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/uploaded-csv-profile.json), [contract](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/harness-reference.md)

## 00:14:53 — The second CSV and the choice of flow data

### 00:14:53 — The UNSW extract has the same broad schema

A tensor shape describes dimensions, not the meaning or origin of the numbers. Your second CSV makes that distinction clearer. The U N S W extract contains seventy nine thousand eight hundred eighty one rows. It has the same broad structure: fifteen hundred payload byte columns followed by time to live, total length, protocol, delta time, and label. There are ten category names. The common column layout makes joint profiling convenient. It does not prove the two files were captured, labeled, or extracted with the same procedure, and it does not make their category names interchangeable.

On screen: 79,881 rows · 1,500 payload columns + 5 metadata fields · 10 label names

Evidence: [csv](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/uploaded-csv-profile.json)

### 00:15:32 — Read the UNSW label distribution

The largest U N S W category is normal, with twenty one thousand rows. Generic contains seventeen thousand five hundred eighty, and exploits contains thirteen thousand nine hundred ninety two. Fuzzers and reconnaissance are also substantial groups. At a high level, reconnaissance means attempts to learn about a target, and fuzzing probes how software handles unusual inputs. These descriptions help interpret the names, but the exact labeling rules come from the dataset's production process. The table is a count of stored labels. It is not a claim that our trained six class model recognizes these ten categories.

On screen: normal: 21,000 · generic: 17,580 · exploits: 13,992

Evidence: [csv](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/uploaded-csv-profile.json)

### 00:16:13 — Rare labels and protocol variety

The remaining labels are do s, backdoor, analysis, shellcode, and worms. Worms has only ninety three rows. Unlike the mostly T C P and U D P protocol entries in the first extract, this file includes a broader range of protocol strings. Some may be uncommon to a beginner, but the practical lesson is simple: a future preprocessing program must handle the actual declared values rather than assume two protocols. The full profile records their counts by label. Again, no packet model was trained on this extract, and these category frequencies do not describe the native flow dataset used in our experiment.

On screen: dos: 3,397 · backdoor: 1,239 · analysis: 1,208 · shellcode: 1,088 · worms: 93

Evidence: [csv](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/uploaded-csv-profile.json)

### 00:16:53 — Related subject, different learning problems

All three data sources concern network traffic, but they define different learning problems. Your C I C I D S extract has fifteen packet label names. Your U N S W extract has ten. The authors' compatible C I C IoT twenty twenty two flow release has six class meanings. A classifier's output layer is tied to its training labels. Six output numbers cannot simply be relabeled with a new ten category vocabulary. Changing the dataset can require a new class mapping, classification head, training protocol, and evaluation. The repository checks that a saved classifier stays attached to the correct class meanings.

On screen: CICIDS2017 CSV: 15 packet labels · UNSW CSV: 10 packet labels · CICIoT2022 flows: 6 native classes

Evidence: [csv](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/uploaded-csv-profile.json), [native](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/native-data-validation.json), [transfer](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/checkpoint-transfer.json)

### 00:17:37 — Why the actual experiment used other data

To exercise the original Net Mamba Plus path, we acquired the authors' native flow release rather than silently fabricate flow context for the CSV rows. The training split has eight thousand three hundred twenty three flows, validation has one thousand forty, and the test split has one thousand forty one. Those three files total ten thousand four hundred four flows. The provided split boundaries were retained. This choice makes the original loader and classifier executable with meaningful inputs. It also means the actual training result is not a result on either of your uploaded CSVs. That distinction belongs in the customer presentation.

On screen: Train: 8,323 flows · Validation: 1,040 flows · Test: 1,041 flows · 6 native classes · Record the departure from the uploaded CSVs

Evidence: [native](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/native-data-validation.json), [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json)

### 00:18:19 — Compatible data still has limitations

Compatibility is not a guarantee of independent evaluation. The validation report found five identical stored inputs shared between training and validation, and six shared between training and test. File names and hashes identify records, but they cannot establish that all physical captures are independent. The released pretrained checkpoint's earlier exposure is also unknown. We preserved the authors' splits and disclosed these issues. A stronger future generalization study would define a new capture independent holdout and document its provenance. Repeating inference on the existing test file checks reproducibility of that result; it does not create a new holdout.

On screen: 5 identical stored inputs across train / validation · 6 across train / test · Capture independence and pretraining exposure remain unknown

Evidence: [native](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/native-data-validation.json), [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json)

### 00:19:04 — The defensible connection between the files

This is the connection between your original three files and the repository. The PDF provides the research method. The CSVs provide packet records that can be profiled, but do not establish the method's required flow context. The repository therefore preserves that finding and runs a compatible native flow experiment instead. If you later obtain raw captures with trustworthy grouping and extraction rules, you can investigate a matching data preparation path. Alternatively, you can explicitly design a packet classifier adaptation. Take ten seconds to explain which data was actually used for the published training runs, and why.

On screen: The paper defines a flow representation · The CSVs reveal an input-contract mismatch · The repository tests a compatible native route

Evidence: [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md), [csv](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/uploaded-csv-profile.json), [native](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/native-data-validation.json)

### 00:19:45 — Your turn · 10 seconds

**Practice pause: 10 seconds.** Which data was actually used for training, and why were the uploaded CSVs not used?

On screen: Which data was actually used for training, and why were the uploaded CSVs not used?

Evidence: [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md), [csv](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/uploaded-csv-profile.json), [native](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/native-data-validation.json)

## 00:19:55 — Follow one native flow into the model

### 00:19:55 — The actual input is a list of flow objects

The actual experiment uses the authors' native flow files. Each file contains a JSON array of flow objects. JSON is structured text with named fields and lists. The data field holds a list of packet byte strings. Sizes and intervals are space separated numeric strings. Labeled examples also carry class information. The small example on screen is synthetic and deliberately shortened to explain the schema. It is not a recovered packet capture. The real loader converts these fields into fixed numerical arrays, so variable length flows can enter the same neural model.

On screen: data: packet byte strings · sizes and intervals: numeric strings · label and name: known training category

Evidence: [native](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/native-data-validation.json), [lesson](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/lesson.md), [contract](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/harness-reference.md)

### 00:20:32 — Bytes: five packets, 320 stored bytes each

The byte branch uses the first five packets and up to three hundred twenty stored bytes from each. Five times three hundred twenty gives sixteen hundred byte positions. Short inputs receive padding and long inputs are truncated. The paper describes an eighty byte header allocation and a two hundred forty byte payload allocation per packet. The released stored bytes can be loaded, but their complete extraction history has not been independently verified. We therefore say stored bytes when describing what our executed loader actually consumed. This preserves the difference between a paper's intended representation and a release's established provenance.

On screen: 5 × 320 = 1,600 stored byte positions · Short inputs are padded; long inputs are truncated · Paper header/payload extraction is not independently verified

Evidence: [lesson](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/lesson.md), [config](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/configs/ciciot2022.json), [paper-notes](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/paper-and-data-explained.md)

### 00:21:13 — Normalization changes the numerical scale

The loader scales a byte value by dividing by two hundred fifty five. It then subtracts one half and divides by one half. Zero becomes negative one, and two hundred fifty five becomes positive one. This puts byte inputs on a common numerical scale. A tensor is simply a multidimensional array of numbers. For a batch of flows, the byte tensor has dimensions batch, one, one, and sixteen hundred. The extra dimensions match the original model's interface. A matching shape is necessary for execution, but it still does not prove that the underlying bytes mean the right thing.

On screen: byte / 255 → range 0 to 1 · Subtract 0.5, divide by 0.5 → range −1 to 1 · Tensor shape: batch × 1 × 1 × 1,600

Evidence: [lesson](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/lesson.md), [config](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/configs/ciciot2022.json)

### 00:21:50 — Sizes and intervals use their own rules

The size branch uses the first twenty packet sizes, clipped between zero and fifteen hundred. Its padding value is clipped to the same upper limit. The timing branch uses the first twenty gaps and maps an observed gap x to one plus x divided by two plus x. Zero maps to one half; one maps to two thirds. Those are numerical examples, not an assertion about seconds. Missing intervals use padding that maps to one. The wrapper requires actual observed gaps to be finite and nonnegative. Training and inference must use the same rules or they present different problems to the model.

On screen: First 20 sizes: clipped to 0 … 1,500 · First 20 gaps: (1 + x) / (2 + x) · Missing values use the loader’s padding rules

Evidence: [lesson](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/lesson.md), [contract](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/harness-reference.md)

### 00:22:30 — The 443-token calculation

A token here is one input unit for the sequence model. It is not a word from a language model. The sixteen hundred byte positions are grouped into four byte strides, producing four hundred byte tokens. Twenty size tokens and twenty interval tokens add forty more. Three learned summary tokens bring the total to four hundred forty three. Each token is embedded into a vector with two hundred fifty six coordinates. An embedding is a numerical representation. The model learns how useful patterns in those coordinates relate to the dataset categories.

On screen: 400 byte tokens · 20 size + 20 interval tokens · 3 summary tokens → 443 total tokens

Evidence: [lesson](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/lesson.md), [config](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/configs/ciciot2022.json)

### 00:23:05 — Four blocks produce six raw outputs

The sequence passes through four Mamba blocks. The active configuration uses the unidirectional branch and its fast execution path. After processing, the three summary vectors are added together and passed to the classification head. The result is six logits, or raw category scores, for each flow. The six class meanings are Flood, R T S P brute force, Audio, Other, Cameras, and Home Automation. Four describe device or activity groups, so these are not six attack types. The complete classifier has one million eight hundred seventy thousand eighty parameters. Parameters are the learned numbers updated during training. They are different from the input tensor values. The runtime checks exercise this complete model rather than replacing it with a smaller lookalike.

On screen: 4 Mamba blocks · width 256 · Combine the 3 summary vectors · Classifier head → 6 logits

Evidence: [lesson](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/lesson.md), [config](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/configs/ciciot2022.json), [support](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/support-matrix.md)

### 00:23:57 — Explain the input contract back

To explain the input contract, cover three levels. The fields must describe the correct flow. Their dimensions and transformations must match the original loader. Finally, the label vocabulary must match the saved classifier. A file can pass a basic JSON parser and still fail one of these requirements. Our wrappers reject incompatible or invalid inputs before model execution where those conditions can be checked. Take ten seconds to describe the three feature views and the six number output, without using the word artificial intelligence as a substitute for the actual process.

On screen: Meaning and origin must match · Dimensions and transforms must match · Class meanings must match the checkpoint

Evidence: [contract](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/harness-reference.md), [lesson](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/lesson.md)

### 00:24:36 — Your turn · 10 seconds

**Practice pause: 10 seconds.** Describe the three feature views and the six-number output.

On screen: Describe the three feature views and the six-number output.

Evidence: [contract](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/harness-reference.md), [lesson](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/lesson.md)

## 00:24:46 — How pretraining, training and inference work

### 00:24:46 — Three activities, three different outputs

Bytes, sizes, and intervals enter the model; six raw scores come out. Now separate learning from using what was learned. Pretraining teaches a representation from a reconstruction task. Fine tuning adapts that representation to known categories using labeled examples. Inference uses a fixed classifier to produce scores without updating its parameters. A checkpoint saves model state so a later process can reload it. Some training checkpoints also include optimizer state and settings. The word checkpoint therefore describes a file's role, not a guarantee that it contains a complete deployment package.

On screen: Pretraining → general representation weights · Fine-tuning → task-specific classifier · Inference → predictions for new inputs

Evidence: [lesson](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/lesson.md), [transfer](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/checkpoint-transfer.json), [runbook](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/runbook.md)

### 00:25:25 — Pretraining hides part of the input

During masked pretraining, parts of the input are hidden or zeroed according to the original procedure. A reconstruction decoder tries to recover the missing content and feature values. The loss measures reconstruction error. The optimizer adjusts parameters to reduce that error over examples. Labels such as Flood or Cameras are not the reconstruction target. Learning a useful representation this way may help a later classification task, but a falling reconstruction loss does not itself prove attack detection accuracy. The full paper uses a much larger pretraining protocol than the short functional check we executed.

On screen: Mask byte content and selected feature values · Reconstruct the missing information · Compare reconstruction with the original values

Evidence: [lesson](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/lesson.md), [runbook](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/runbook.md), [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json)

### 00:26:05 — What our pretraining check actually did

Our limited check completed two epochs and one hundred thirty two optimizer updates on downstream training data. Reconstruction loss fell from about nine point five two to six point one three. The requested short step budget was rounded by the original loop to complete epochs. This demonstrates that the masked training path executes and learns on that check. It does not recreate the paper's one hundred fifty thousand step pretraining. The three main fine tuning runs started from the authors' released pretrained checkpoint, not the output of our short check. Keep those two branches separate when drawing the workflow.

On screen: 2 completed epochs · 132 updates · Loss: 9.51953 → 6.12702 · Separate from the checkpoint used for full fine-tuning

Evidence: [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json), [transfer](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/checkpoint-transfer.json), [runbook](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/runbook.md)

### 00:26:44 — A labeled batch changes the classifier

In fine tuning, a batch contains multiple labeled flows. The forward pass computes category scores. A classification loss compares those scores with the supplied labels, with the configured smoothing. The backward pass computes gradients, which describe how parameter changes affect the loss. The optimizer then updates those parameters. Repeating this process across the training loader forms an epoch. A learning rate controls the scale of updates. This is why training needs much more computation than simply opening the recorded demo. The demo reads saved outputs; a training command repeatedly changes the model.

On screen: Forward pass → predictions · Loss → mismatch with known labels · Backward pass + optimizer → updated parameters

Evidence: [lesson](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/lesson.md), [config](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/configs/ciciot2022.json), [runbook](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/runbook.md)

### 00:27:25 — Three splits prevent one obvious shortcut

The training split supplies parameter updates. Validation results select a checkpoint. The test split measures the selected classifier's performance afterward. Choosing a checkpoint by its test score would use the test set as a tuning signal. The native fine tuner selects the best validation accuracy and then performs its final test pass. Separate evaluation strictly reloads that selected classifier. This separation is necessary, although the previously disclosed input overlaps and unknown capture history still limit the evidence. Following the split procedure cannot undo uncertainty in how the underlying data was collected.

On screen: Training split: update parameters · Validation split: choose the checkpoint · Test split: measure the selected classifier

Evidence: [native](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/native-data-validation.json), [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json), [runbook](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/runbook.md)

### 00:28:08 — The completed training protocol

Each of the three declared seeds completed one hundred twenty epochs and seven thousand nine hundred twenty updates. A seed sets the starting values for randomized operations; the seeds are not three independent datasets. The source based recipe uses batch size one hundred twenty eight and a base learning rate that resolves to an effective rate of zero point zero zero one. The paper describes different batch and runtime conditions. Our training ran without mixed precision, while native evaluation used its recorded mixed precision path. These details help another engineer reproduce our execution rather than accidentally claim an exact paper configuration.

On screen: Seeds 0, 1 and 2 · 120 epochs and 7,920 updates per run · Batch 128; effective learning rate 0.001

Evidence: [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json), [config](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/configs/ciciot2022.json), [runbook](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/runbook.md)

### 00:28:51 — A successful reload has a narrow meaning

Strict reloading rejects missing or unexpected model tensors rather than quietly ignoring them. The wrapper also checks the class meaning associated with each output index. This matters because a numerically valid classifier could otherwise display the wrong category names. Inference can return logits, display scores, and a selected class for unlabeled flows. It cannot calculate accuracy without ground truth. Take ten seconds: explain the difference between demonstrating a short pretraining update, completing fine tuning, and using a saved classifier to predict. Name the separate output produced by each activity.

On screen: Strict loading checks all expected tensors · Model state and class meanings must stay together · New accuracy requires known labels

Evidence: [transfer](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/checkpoint-transfer.json), [contract](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/harness-reference.md), [runbook](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/runbook.md)

### 00:29:33 — Your turn · 10 seconds

**Practice pause: 10 seconds.** What does each of pretraining, fine-tuning and inference produce?

On screen: What does each of pretraining, fine-tuning and inference produce?

Evidence: [transfer](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/checkpoint-transfer.json), [contract](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/harness-reference.md), [runbook](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/runbook.md)

## 00:29:43 — The main code: follow a real execution path

### 00:29:43 — Our code surrounds the authors’ code

Pretraining produces representation weights, fine tuning produces a task specific classifier, and inference produces predictions. Now follow the code that organizes those activities. This repository is an execution and evidence layer around the authors' source. It does not claim authorship of Net Mamba Plus. The source is fetched at a pinned commit, with a recorded inventory of one hundred three source files and additional core hashes. Keeping the original loader avoids writing a second interpretation of byte padding and normalization. The surrounding code supplies validation, reproducible commands, manifests, and independent output checks.

On screen: Acquire and verify the original source · Invoke the original loader and model · Record execution and check its outputs

Evidence: [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md), [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md), [config](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/configs/ciciot2022.json)

### 00:30:25 — repro.py is the experiment coordinator

The main entry point is repro dot p y. Its commands acquire or validate the pinned source and data, resolve the original command line settings, and launch training subprocesses. A subprocess is a separately running program invoked by the coordinator. The wrapper creates a fresh output directory and a manifest recording identities, configuration, environment, and status. A failed job should leave an informative record. It should not overwrite a prior successful result and make the two runs impossible to distinguish. Shared preparation helpers are reused by the other entry points.

On screen: fetch and validate · pretrain and finetune · Fresh output directories and run manifests

Evidence: [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md), [contract](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/harness-reference.md)

### 00:31:04 — evaluate.py answers: how accurate is this model?

Evaluate dot p y loads a saved classifier strictly and evaluates labeled test flows through the original loader and evaluation engine. It does not train the model again. It also does not choose a checkpoint by maximizing test accuracy. Its result is a set of metrics attached to the evaluated model and data. If someone sends you a number without a checkpoint identity or class mapping, you cannot establish that it describes the intended classifier. This wrapper records those bindings so the reported accuracy can be traced to a particular execution.

On screen: Labeled native test flows · Strict saved-classifier loading · Native evaluation metrics

Evidence: [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md), [runbook](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/runbook.md), [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json)

### 00:31:40 — Predict a class, then calibrate its confidence

Predict dot p y accepts native flows whose true categories are unknown. It uses the original loader, discards targets before the model runs, and returns a class name, logits, and raw scores. The new calibration module can also divide those logits by one positive number called a temperature, then compute a second set of scores. The largest logit stays largest, so the predicted class does not improve or change. Tools slash calibrate dot p y fits that number from validation labels. The calibration file records the checkpoint, configuration, class meanings, and runtime that it belongs to.

On screen: predict.py keeps raw logits and class names · calibration.py adjusts scores with one temperature · tools/calibrate.py fits on validation labels only

Evidence: [calibration](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/confidence-calibration.md), [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md), [contract](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/harness-reference.md)

### 00:32:20 — replay.py connects execution to explanation

Replay dot p y records labeled model predictions and independently recomputes metrics from the saved outputs. It also builds the self contained browser demonstration. The browser page displays the data already written into it. It does not need CUDA or a model checkpoint to replay those results. This split is intentional: the numerical experiment can be reviewed once and then explained on another computer without rerunning training. The tradeoff is that the page is a recorded demonstration. New customer flows require actual inference through a checked runtime, not just a browser refresh.

On screen: Run labeled inference · Save per-flow results and independent metrics · Generate a browser page from those records

Evidence: [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md), [prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/seed0/replay/predictions.json)

### 00:32:58 — Configurations and assets define the recipe

The configuration files are recipes and identity checks. They contain settings, source pins, expected asset hashes, and class metadata. The assets directory holds separately acquired data and weights on your machine. The downloaded authors' source lives in the local upstream slash Net Mamba Plus directory. Those external assets are not mirrored as public repository contents. This distinction explains why cloning the repository is enough for document checks but not enough for neural training. The acquisition tools must obtain the additional files, verify their identities, and preserve their unresolved inherited redistribution and commercial terms.

On screen: configs: settings, hashes and class mapping · assets: downloaded data and weights, kept locally · upstream/NetMambaPlus: pinned source, kept locally

Evidence: [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md), [config](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/configs/ciciot2022.json), [transfer](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/checkpoint-transfer.json)

### 00:33:42 — Read a run in this order

When auditing a run, start with its manifest. Then inspect the log and the saved metrics or predictions. A configuration file proves what was requested, not that the run completed. A model file proves saved state exists, not which data produced it. A chart is a presentation of measurements, not their origin. The records work together. Take ten seconds to decide which entry point you would use for an unlabeled native flow, and which one you would use to score a labeled test set. Then identify the file that records the run's provenance.

On screen: Manifest: what was requested and what completed · Log: what execution reported · Metrics and predictions: what was measured

Evidence: [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md), [verification](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/verification.md)

### 00:34:16 — Your turn · 10 seconds

**Practice pause: 10 seconds.** Which scripts handle unlabeled prediction and labeled evaluation? Where is run provenance recorded?

On screen: Which scripts handle unlabeled prediction and labeled evaluation? Where is run provenance recorded?

Evidence: [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md), [verification](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/verification.md)

## 00:34:26 — Read the actual results, including the mistakes

### 00:34:26 — Three runs, one fixed test set

Use predict for unlabeled flows, evaluate for labeled scoring, and the manifest for run provenance. Now examine the recorded results. Seed zero correctly classified nine hundred fifty of one thousand forty one test flows. Seed one got eight hundred seventy five correct. Seed two got eight hundred eighty one. Those correspond to ninety one point two six, eighty four point zero five, and eighty four point six three percent accuracy. All three results are retained. Selecting only the strongest seed would give a misleading impression of this training procedure's observed variability.

On screen: Seed 0: 91.26% · 950 / 1,041 correct · Seed 1: 84.05% · 875 / 1,041 correct · Seed 2: 84.63% · 881 / 1,041 correct

Evidence: [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json)

### 00:35:05 — Mean and spread answer different questions

The average accuracy is eighty six point six five percent. The sample standard deviation is four percentage points. The mean summarizes these three runs; the standard deviation summarizes their spread. It is not a confidence interval and does not prove how performance will vary on a customer's network. All three seeds used the same test split. One result has therefore been repeated under different randomized training conditions, rather than evaluated on three independently collected networks. Those are useful measurements, but they answer a narrower question than real world generalization.

On screen: Mean: 86.65% · Sample standard deviation: 4.00 percentage points · Not a confidence interval or an independent holdout study

Evidence: [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json), [native](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/native-data-validation.json)

### 00:35:43 — Accuracy, precision, recall and F1

Accuracy counts correct predictions across the full test set. Precision asks how many predictions of a category were right. Recall asks how many actual examples of that category were found. F one combines precision and recall. Macro F one treats categories equally, while weighted F one accounts for how many true examples each category has. These metrics can disagree when class sizes differ or errors concentrate in one category. The repository preserves independent metrics and a confusion matrix so you can inspect the pattern, rather than trust a single percentage.

On screen: Accuracy: correct predictions / all predictions · Precision: how often a predicted category is right · Recall: how much of a true category was found

Evidence: [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json), [prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/seed0/replay/predictions.json)

### 00:36:22 — Read a confusion matrix

In the matrix, each row is a known category and each column is the model's prediction. Counts on the diagonal are correct. Off diagonal counts show which categories were confused. Our test set has two hundred examples for each category except Other, which has forty one. That support difference matters when comparing percentages. The matrix is computed from saved predictions, so another reviewer can recompute it. A large diagonal is encouraging, but the mistakes remain important: an operational system must understand the cost of both missed attacks and incorrect alerts on benign activity.

On screen: Rows: known category · Columns: predicted category · Off-diagonal cells are mistakes

Evidence: [prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/seed0/replay/predictions.json), [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json)

### 00:37:02 — Fresh checks ran on the actual GB10

The testing was rerun on the actual G B ten. Seven CUDA operator comparisons passed against reference calculations. The complete original model produced finite gradients, changed its weights in an optimizer step, saved, and reloaded strictly. This was a functionality test using six synthetic fixtures, not another full training experiment. Three fresh seed zero inference runs also retained every one of the one thousand forty one recorded class predictions. Some half precision logits differed slightly from the older recording, by at most zero point zero zero three nine zero six two five. We preserve that difference rather than promise bitwise reproducibility.

On screen: 7 CUDA operator comparisons passed · Complete model: real optimizer step and strict reload · 1,041 classes match; tiny FP16 logit differences remain

Evidence: [gb10-current](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/calibration/gb10-baseline-audit.json), [verification](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/verification.md), [support](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/support-matrix.md)

### 00:37:46 — The paper gap is still an open question

The paper comparison is higher than our measured result. Possible contributing factors include runtime differences, training settings, extraction details, and checkpoint history, but we have not isolated their effects. Naming plausible causes is not the same as testing them. A defensible follow up would change one relevant factor under a controlled protocol and retain every outcome. It would also address data independence and record exact preprocessing. For now the accurate statement is that the model executes and trains, while the paper's headline accuracy has not been reproduced under our measured conditions.

On screen: Paper: different runtime and training conditions · Released checkpoint history is incomplete · No experiment has isolated the gap’s cause

Evidence: [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json), [config](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/configs/ciciot2022.json), [comparison](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/upstream-comparison.md)

### 00:38:27 — Measured confidence improves; accuracy is unchanged

All three confidence measures improved for every checkpoint. Mean negative log likelihood fell from zero point four four one six to zero point four one seven two. Mean Brier score fell from zero point two zero three five to zero point two zero one two. Expected calibration error fell from seven point zero three percent to three point eight two percent. Lower is better for these measures. Accuracy stayed unchanged. This retrospective comparison reuses validation and already seen test data. Take ten seconds to explain our mean accuracy and spread without claiming customer validation.

On screen: Mean NLL: 0.4416 → 0.4172 · Mean Brier: 0.2035 → 0.2012 · Mean ECE: 7.03% → 3.82%

Evidence: [calibration](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/confidence-calibration.md), [calibration-results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/calibration/results.json), [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json)

### 00:39:11 — Your turn · 10 seconds

**Practice pause: 10 seconds.** Explain the mean and spread without claiming customer-network validation.

On screen: Explain the mean and spread without claiming customer-network validation.

Evidence: [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json), [verification](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/verification.md)

## 00:39:21 — Demonstrate one prediction, then reveal an error

### 00:39:21 — Open the recorded replay

Now use the browser replay to make the result concrete. The page can be opened on a presentation machine without installing CUDA, Python, or a checkpoint. It displays seed zero's saved predictions and their known labels. Its controls let you inspect the recorded sequence and errors. The screenshot comes from the actual working page. This is a good customer demonstration because the evidence is available offline and can be inspected consistently. Say recorded replay before presenting it, so a moving table is not mistaken for a live packet feed.

On screen: Runs without a GPU or Python · Displays saved seed-0 predictions · Opening it does not run new inference

Evidence: [prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/seed0/replay/predictions.json), [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md)

### 00:39:56 — Choose the demo model before inspecting outcomes

Seed zero was declared as the demonstration model. The other two results remain published beside it. A demo often needs one fixed model and a manageable story, but that choice must not hide variability. Also, the number of predictions assigned to attack categories is not the number of operational security alerts. A real alert policy might combine repeated observations, thresholds, exceptions, and analyst context. Those policy components have not been implemented here. The recorded page lets you explain classification behavior; it does not establish an incident response workflow.

On screen: Seed 0 is the declared demonstration model · All three seeds remain visible in the results · A convenient demo is not a new evaluation protocol

Evidence: [prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/seed0/replay/predictions.json), [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json), [answers](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/answers.md)

### 00:40:36 — Inspect JSON row 635

Look at the saved prediction with JSON index six hundred thirty five. The browser numbers rows from one, so it displays that record as zero six three six. The highest score belongs to R T S P brute force. Its normalized display score is eighty four point four three percent. Before looking at the true label, notice how confident that display can appear. Softmax converts six logits into scores that add to one. That arithmetic does not establish that the top score is a calibrated probability of an attack.

On screen: Browser display row: 0636 · Highest score: RTSP Brute Force · Display score: 84.43%, not a calibrated attack probability

Evidence: [prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/seed0/replay/predictions.json)

### 00:41:10 — Reveal the known label

The known label is Other. This prediction is wrong. That single record gives you a useful way to explain why a high display score is not sufficient evidence to block traffic. The model must assign one of its known categories, even when a flow is ambiguous or unlike its training examples. The project has no validated unknown attack detector. Its new calibration results do not establish reliability on customer traffic. This real mistake exposes the gap between classifier output and an operational security decision.

On screen: True category: Other · Predicted category: RTSP Brute Force · This confident-looking prediction is wrong

Evidence: [prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/seed0/replay/predictions.json)

### 00:41:46 — Use the optional calibrated inference path

To use the new feature, first run the calibration command on validation flows with the frozen checkpoint. Then supply that calibration file to predict dot p y. A threshold of zero point nine accepts a result only when its calibrated top class score reaches that value; lower scores are marked defer. The original prediction remains in both cases. Missing, malformed, or incompatible calibration files cause an explicit failure. These are new model executions outside the browser. This interface is a useful component for a future service, but capture, flow creation, and customer data validation still need to be built around it.

On screen: Fit calibration.json from validation data first · Keep original class, logits and raw scores · Add calibrated scores and accept/defer decisions

Evidence: [calibration](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/confidence-calibration.md), [contract](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/harness-reference.md)

### 00:42:27 — Accept or defer is a review policy

Here is the tradeoff behind that threshold. For seed zero, the raw scores accepted six hundred twenty flows, with nine wrong. Calibrated scores accepted eight hundred ninety three flows, with thirty seven wrong. So the calibrated policy deferred fewer predictions, while accepting more errors. Acceptance is not a safety guarantee. Coverage means accepted divided by all rows; accepted error means wrong accepted divided by accepted. When nothing is accepted, that error is undefined, not zero. This is a fixed demonstration threshold on already seen research data. Capture, independently labeled customer traffic, and operational response rules still need validation.

On screen: Raw scores: 620 accepted flows; 9 wrong flows · Calibrated: 893 accepted flows; 37 wrong flows · Fewer deferrals, more accepted errors

Evidence: [calibration](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/confidence-calibration.md), [calibration-results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/calibration/results.json), [hardware](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/hardware-roadmap.md)

### 00:43:14 — Practice the demonstration handoff

To hand this demo to another presenter, show the saved result, reveal the incorrect example, and explain the missing operational stages. Keep the native inference command available for an engineer who wants to run new compatible flows. Keep the offline replay available for a meeting with unreliable internet. Neither route needs a chatbot to classify traffic. Take ten seconds to explain why the eighty four point four three percent score was not enough to trust this particular prediction, even though the score calculation itself was valid.

On screen: Show the replay and one actual error · State what runs locally and what is recorded · Separate a category score from an alert policy

Evidence: [prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/seed0/replay/predictions.json), [answers](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/answers.md)

### 00:43:50 — Your turn · 10 seconds

**Practice pause: 10 seconds.** Why was the 84.43% display score insufficient to trust this prediction?

On screen: Why was the 84.43% display score insufficient to trust this prediction?

Evidence: [prediction](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/seed0/replay/predictions.json), [answers](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/answers.md)

## 00:44:00 — Set it up, use it and test the right layer

### 00:44:00 — Choose one of three setup routes

The score was uncalibrated and the known label showed an error. Next, choose the setup you actually need. For a presentation, use the video, documents, and recorded browser demo. For portable evidence checks, use Git and Python. For new neural training or inference, use the checked Linux CUDA environment and separately acquired assets. These routes have different requirements. A laptop can display the presentation without supporting the model's CUDA extensions. This separation makes the project usable on other systems while keeping the model execution claims tied to hardware that was actually tested.

On screen: Present: browser or document viewer · Recheck: Git and Python · Execute the model: checked Linux CUDA environment

Evidence: [support](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/support-matrix.md), [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md)

### 00:44:38 — Clone and run the portable checks

For the portable route, clone the repository, enter its directory, and run the commands shown. Use Python three if that is your system's executable name. The unit tests and the package and video source checks use the standard library without downloading research data. A successful suite ends with O K, and the verifiers exit successfully. These checks protect important behavior such as input rejection, file identity, and consistent published artifacts. They are deliberately different from a GPU training test. Read the workflow record for the exact test count and commit that passed.

On screen: Clone the current repository · Run the unit suite and package checks · These checks do not download or train the model

Evidence: [support](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/support-matrix.md), [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md)

### 00:45:15 — What cross-platform CI establishes

The automated workflow runs the portable checks on Linux and Windows with x eighty six processors, and macOS on ARM, using Python three point ten and three point twelve. That makes six combinations. Earlier failures exposed text encoding, newline, and temporary directory issues. Those were corrected and retained as regression tests rather than removing platforms from the matrix. A green workflow means those particular checks passed on the recorded commit. It does not establish native Windows or macOS execution of the original neural model. The support matrix keeps those boundaries separate.

On screen: Linux x86-64, Windows x86-64, macOS ARM64 · Python 3.10 and 3.12: six combinations · Hosted jobs run portable checks, not GPU training

Evidence: [support](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/support-matrix.md), [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md)

### 00:45:55 — The model environment has native dependencies

The GPU route uses a specific environment profile. It includes Python three point twelve, Torch two point nine point one with CUDA thirteen, and pinned native extensions for Mamba and causal convolution. These extensions contain compiled GPU code. A compatible Python package name alone is not enough: the driver, compiler, selected GPU architecture, and installed binaries must work together. The current support guide provides the full commands. The generalized builder uses disposable source copies, checks the selected target, and records actual compiler flags. It preserves the original model's source identity.

On screen: Python 3.12 · Torch 2.9.1 + CUDA 13.0 · Pinned Mamba and causal-convolution extensions · Compiler, driver and GPU architecture must agree

Evidence: [support](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/support-matrix.md), [config](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/configs/ciciot2022.json)

### 00:46:37 — Pass two gates before a new experiment

After building, run the numerical checker and the complete model checker. The numerical checker compares selected GPU operations with reference computations. The complete model checker processes six synthetic fixtures through all four blocks, performs an optimizer update, saves and strictly reloads the state, and checks inference. It can bind installed extension hashes to the completed build report. This catches failures that a successful import would miss. Synthetic fixtures prove functionality, not accuracy. Only after those gates pass should you acquire and validate the real flow assets and start a new measured experiment.

On screen: Numerical check: forward and backward comparisons · Complete-model check: update, save, reload, infer · Keep the build report with the runtime results

Evidence: [support](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/support-matrix.md), [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md)

### 00:47:18 — Know what is still platform-specific

The original model has measured execution on G B ten. A fresh environment on that same hardware also passed the generalized build and model checks. Other physical NVIDIA GPUs still need their own validation. There is no complete CPU model fallback, Apple graphics backend, or validated N P U implementation. Some reference formulas exist, but normal imports and active execution still depend on CUDA and fused operations. If a setup fails, inspect the fresh build report and logs. Do not turn off checks until it appears green; determine which prerequisite or computation actually failed.

On screen: GB10: measured training and inference · Other NVIDIA GPUs: build route, machine-specific validation needed · CPU, Apple MPS, NPU: no validated model backend

Evidence: [support](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/support-matrix.md)

### 00:48:00 — Match the test to the claim

You can now explain setup without promising that every machine runs every layer. Use the simplest route for the job. Preserve output directories and their manifests. Read failures before retrying with a corrected configuration. When someone asks whether it works elsewhere, specify whether they mean opening the materials, rechecking evidence, or running the neural model. Take ten seconds to choose the correct route for a colleague who only needs to present the demo on a Windows laptop, and the separate route for an engineer who wants new GPU predictions.

On screen: Document checks → package integrity · GPU gates → execution correctness within their scope · Labeled holdout → measured predictive performance

Evidence: [support](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/support-matrix.md), [verification](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/verification.md)

### 00:48:35 — Your turn · 10 seconds

**Practice pause: 10 seconds.** Which setup is enough to present, and which setup is needed for new model predictions?

On screen: Which setup is enough to present, and which setup is needed for new model predictions?

Evidence: [support](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/support-matrix.md), [verification](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/verification.md)

## 00:48:45 — Every repository area and every download

### 00:48:45 — Use the file guide as the complete index

A presenter needs the viewing route; new neural predictions require the checked GPU route. Now tour the rest of the repository. The file guide is the complete inventory, with one entry for every tracked file. This chapter explains how the areas fit together so that the inventory is useful instead of becoming a wall of unfamiliar names. Tracked means included in Git. Locally downloaded source, raw data, checkpoints, environments, and temporary runs are separate. A GitHub release attachment is another separate object: it belongs to its tagged release, not automatically to the current working tree.

On screen: One entry for every tracked file · Separate explanations for local downloads and run outputs · Links take you from an explanation to its evidence

Evidence: [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md)

### 00:49:25 — Root files, configuration and dependencies

At the root, the read me is the front door and the four Python entry points coordinate execution. Configs contains the source based fine tuning recipe, the short pretraining recipe, and the asset inventory. Requirements separates packages used for different activities, such as GPU execution, browser checks, and video production. Dot git ignore keeps local outputs and sensitive settings out of normal tracking. Dot git attributes preserves the exact bytes of recorded documents and configurations across platforms. Neither file establishes data rights or scientific correctness; they support reliable repository handling.

On screen: README and four entry points: start and execute · configs: experiment recipes and identities · requirements: packages grouped by activity

Evidence: [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md)

### 00:50:07 — Tools: acquire, build, measure and calibrate

The tools directory contains programs that support the experiment. Fetch assets obtains verified external files, while profile C S Vs scans the uploaded data. The CUDA builders compile pinned extensions; operator and complete model checks test their behavior. Benchmark measures model timing, and probe export records whether a computation graph can be captured. The new calibration command reads validation flows and writes a checkpoint bound temperature file with fit evidence. Publish evidence copies reviewed records into the package; its name does not mean arbitrary files are automatically sent to GitHub. The file guide explains every tool's inputs, outputs, and purpose.

On screen: Acquire assets and profile the two CSVs · Build CUDA, test operators and check the full model · Fit calibration; measure confidence and review coverage

Evidence: [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md), [calibration](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/confidence-calibration.md)

### 00:50:54 — Tools: documents, replay and this video

Other tools build the customer package, the plain language learning guide, replay outputs, and teaching materials. The video pipeline separates the lesson source, speech rendering, visual assembly, and browser page. Codex authors the narration and explanations. Microsoft's Andrew neural voice converts that text into sound; the speech service does not research or write the lesson. Verification tools compare identities and inspect encoded media. The archived interactive course builders remain for reference continuity, but the retired public course route is excluded from deployment. The one active video is the current teaching path.

On screen: Package and guide builders produce teaching artifacts · Replay rendering and recording preserve demonstrations · Narration, video and page builders share one lesson source

Evidence: [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md)

### 00:51:35 — Tests, workflows, documents and evidence

Tests contains controlled cases for the wrappers, acquisition, portability, runtime checking, and presentation tooling. The workflow files run portable checks and publish the selected browser material. Docs contains foundational explanations and the customer package. Figures are reusable charts; evidence contains original experiment records; audit evidence contains later rechecks. Research records preserve plans and council outcomes. A council discussion can improve a design, but it is not an executed GPU test. An unratified review remains unratified even when ordinary implementation later fixes a technical problem. Read the status and evidence scope of each record.

On screen: tests: controlled regression cases · workflows: portable CI and Pages publication · docs: explanations, evidence, audits and research records

Evidence: [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md), [verification](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/verification.md)

### 00:52:22 — Choose the right download

The original customer release contains a briefing PDF, editable PowerPoint, slide PDF, offline package, and supporting presentation materials at its recorded revision. It remains a frozen experiment package. The new course has its own versioned video, transcript, captions, and companion materials. A transcript is the narration in text. Caption files add time boundaries for video players. Chapter metadata supports navigation, and the media manifest records hashes and provenance. Use the current support matrix for later portability work. Do not assume the original release ZIP silently changes whenever the repository gains a new file.

On screen: Current course: one MP4, transcript, captions and companion slides · Historical customer bundle: fixed original experiment package · Current support matrix: latest tested setup boundaries

Evidence: [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md), [support](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/support-matrix.md)

### 00:53:06 — A practical reading order

For a new colleague, begin with the read me and this course, then use the file guide to explore a specific task. Before running commands, read the current support matrix and the runbook. Before presenting a result, trace it from the results document to its manifest, log, and predictions. You do not need to memorize every audit JSON file. You need to know which question it answers and how it was produced. Take ten seconds to choose the file you would open to check a platform claim, and the record you would open to verify an actual training result.

On screen: README → course → file guide · Runbook and support matrix before executing commands · Results → manifests → logs when checking a claim

Evidence: [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md), [support](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/support-matrix.md), [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json)

### 00:53:40 — Your turn · 10 seconds

**Practice pause: 10 seconds.** Where would you verify a platform claim and an actual training result?

On screen: Where would you verify a platform claim and an actual training result?

Evidence: [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md), [support](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/support-matrix.md), [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json)

## 00:53:50 — Hardware roadmap, missing work and your handoff

### 00:53:50 — Keep the measured timing boundary visible

Use the support matrix for platform claims and the run records for training evidence. Finally, consider hardware deployment. The model only benchmark measured a median batch one latency of about zero point eight eight milliseconds on G B ten. It used twenty warmup iterations and one hundred measured repetitions. That timing excludes packet capture, waiting for enough packets, preprocessing, transfers, model loading, and alert handling. A fast classifier can still be part of a slow pipeline. End to end latency must be measured across the complete path a real observation follows.

On screen: Batch 1 median: 0.881265 ms · Measured on GB10 after warmup · Excludes capture, flow waiting, preprocessing and transfers

Evidence: [benchmark](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/benchmark/metrics.json), [hardware](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/hardware-roadmap.md)

### 00:54:28 — A possible SmartNIC and NPU division

A network interface card moves traffic into and out of a machine. A Smart N I C can take on additional packet handling or computation. An N P U accelerates neural operations that its runtime supports. A possible future division places capture and some flow handling near the network interface, with a host coordinating buffers, features, inference, and alert policy. This is an architectural proposal. Our repository has not executed Net Mamba Plus on a Smart N I C or N P U, and it does not establish a direct memory transfer path on the measured hardware.

On screen: NIC / SmartNIC: packet handling and flow assembly · Host: orchestration, buffering and policy · NPU: supported neural computation after a verified port

Evidence: [hardware](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/hardware-roadmap.md)

### 00:55:04 — Weights are not a portable computation graph

A model only checkpoint export saves parameter tensors without the training optimizer. A graph export tries to represent the computation for another execution system. These are different operations. Our strict graph capture probe failed at the custom causal convolution CUDA operator, while ordinary eager GPU inference works. Copying the weight file to an N P U therefore does not solve deployment. A port needs supported operators or equivalent implementations, compatible layouts, controlled precision, and numerical validation against the known outputs. The recorded failure is useful because it identifies a concrete obstacle rather than a vague future optimization.

On screen: Model-only export: saved parameter tensors · Graph export: represent the computation for another runtime · Tested strict graph capture failed at a custom CUDA operator

Evidence: [export](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/export-probe/metrics.json), [hardware](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/hardware-roadmap.md), [transfer](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/checkpoint-transfer.json)

### 00:55:48 — A defensible hardware validation process

After implementing a target backend, first compare its full model outputs with the checked reference. Where training is part of the target, compare gradients as well. If reducing numerical precision through quantization, measure the effect on the labeled task instead of assuming the same accuracy. Then measure throughput, tail latency, memory, buffering, and packet drops under an actual traffic path. A compiler success message proves a build stage, not useful security behavior. Only a complete measured pipeline can support a deployment claim, and none of those N P U or Smart N I C measurements exists here yet.

On screen: Check full-model output and gradient parity where relevant · Measure quantization accuracy on labeled data · Measure throughput, tail latency, buffering and drops

Evidence: [hardware](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/hardware-roadmap.md), [support](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/support-matrix.md)

### 00:56:28 — What remains missing

The new calibration experiment improves the project's confidence handling, but it does not close the main research and deployment gaps. We have not matched the paper accuracy, repeated its full pretraining, or established live capture and extraction. Calibration was fitted using data already involved in checkpoint selection, and the test set was already seen. Its behavior on independent customer traffic remains unknown. Unknown attack detection, operational alert guarantees, and an N P U deployment are still missing. Other physical GPUs need their own execution checks. These limits stay beside the positive evidence, including the results that did not improve.

On screen: Matching paper accuracy and full pretraining · Independent calibration and customer-network validation · Live extraction, unknown attacks and hardware deployment

Evidence: [calibration](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/confidence-calibration.md), [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json), [hardware](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/hardware-roadmap.md), [support](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/support-matrix.md)

### 00:57:12 — Teach the project to someone else

Now explain the project aloud in your own words. Start with the paper's idea, distinguish the uploaded packet files from the training flows, and follow inputs through training and inference. Give the measured result and one real error. Explain what the repository adds and which setup your listener needs. Finish with the remaining deployment work. You have ninety seconds, and you can pause longer. The transcript, slides, and every file guide remain available afterward. Your strongest presentation is one in which each claim leads to evidence and each limitation leads to a clear next test.

On screen: What data went in, and why? · What was executed and measured? · What remains before customer deployment?

Evidence: [answers](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/answers.md), [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md), [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json)

### 00:57:51 — Your turn · 90 seconds

**Practice pause: 90 seconds.** Explain the data choice, tested result, repository and remaining deployment work.

On screen: Explain the data choice, tested result, repository and remaining deployment work.

Evidence: [answers](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/answers.md), [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md), [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json)

### 00:59:21 — Your concise explanation

Here is a concise handoff. We built a checked execution and evidence layer around the authors' original Net Mamba Plus model. We profiled the two uploaded packet CSVs and established why they were not compatible flow inputs. Using the authors' native flow data, three full training runs averaged eighty six point six five percent test accuracy. The repository includes strict inference, independent results, a recorded demo, setup checks, and teaching materials. The paper number and a live deployed intrusion detection system remain unproven by this work.

On screen: We built a checked execution and evidence layer · The original model trained on compatible native flows · Measured results and limits are both available

Evidence: [answers](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/answers.md), [results](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/customer/evidence/results.json), [walkthrough](https://github.com/buffbeefalo/netmambaplus-reproduction/blob/main/docs/repository-walkthrough.md)
