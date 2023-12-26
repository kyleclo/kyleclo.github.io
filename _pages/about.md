---
layout: about
title: about
permalink: /
<!-- subtitle: <a href='#'>Affiliations</a>. Address. Contacts. Moto. Etc. -->

profile:
  align: right
  image: kyle_lo_profile.jpg
  image_circular: false # crops the image to make it circular
  <!-- address: <p>555 your office number</p> <p>123 your address street</p> <p>Your City, State 12345</p> -->

personal: true  # includes bio of personal info
news: true  # includes a list of news items
selected_papers: false # includes a list of papers marked as "selected={true}"
social: true  # includes social icons at the bottom of the page
---

Lead Scientist at the [Allen Institute for AI](https://allenai.org/). I co-lead open dataset development for the [OLMo](https://allenai.org/olmo) project. I also work on human-centered AI for scientific research assistance with the [Semantic Scholar Research](https://www.semanticscholar.org/research/research-team) team.

##### ▸ Open Datasets for AI Development
<!-- ##### ▸ Datasets for open science -->

<!-- I curate and release large-scale, high-quality datasets and corpora to support an open ecosystem for AI development. -->

In 2020, I developed [S2ORC](https://aclanthology.org/2020.acl-main.447), the largest, machine-readable collection of open-access full-text papers to-date, and [CORD-19](https://aclanthology.org/2020.nlpcovid19-acl.1/), the most comprehensive, continually-updated set of COVID-19 literature at the time.

In 2023, I released [Dolma](https://huggingface.co/datasets/allenai/dolma), the largest open dataset for language model pretraining to-date, which included [peS2o](https://huggingface.co/datasets/allenai/peS2o), a transformation of S2ORC optimized for training language models of science.

##### ▸ Beyond Web Text: Language Models for Specialized Texts

<!-- ##### ▸ Language models beyond web text -->

<!-- Can we adapt language models trained on broad web crawls to perform well on specialized texts, like scientific articles or legal documents? -->

In 2019, I developed [SciBERT](https://aclanthology.org/D19-1371), one of the first pretrained language models for scientific text. In 2020, my work on domain adaptation via [continued pretraining](https://aclanthology.org/2020.acl-main.740/) of language models won an honorable mention for best paper at ACL 🏆.

Language models should also work well on visually-rich documents like PDFs. I develop methods for [infusing language models with visual layout](https://aclanthology.org/2022.tacl-1.22/). In 2023, I packaged these models into [PaperMage](https://aclanthology.org/2023.emnlp-demo.45/), an open-source Python library that won a best paper award for ACL System Demos 🏆.

Since 2023, I've been working on out-of-domain generalization for retrieval with language models, through [parameter-efficient training](https://arxiv.org/abs/2311.09765) and [data augmentation](https://arxiv.org/abs/2309.08541).


##### ▸ Standards, Unexplored Directions, and Best Practices in NLP Evaluation

I've organized community shared tasks to evaluate NLP systems for biomedical literature retrieval and understanding, including [TREC-COVID](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7239098/) and [SCIVER](https://aclanthology.org/2021.sdp-1.16/). I've also worked on standardized benchmark development for [domain fit](https://arxiv.org/abs/2312.10523) and [efficiency](https://arxiv.org/abs/2307.09701) of language models.

I've identified surprising weaknesses in today's language models in [multidocument summarization](https://aclanthology.org/2023.findings-emnlp.549/), [book-length summarization](https://arxiv.org/abs/2310.00785), [visual layout parsing](https://aclanthology.org/2023.findings-acl.844/), and [snippet decontextualization](https://aclanthology.org/2023.emnlp-main.193/).

I've designed evaluation guidelines for NLP, including [few-shot learning](https://openreview.net/forum?id=_WnGcwXLYOE) and [long-form summarization](https://aclanthology.org/2023.eacl-main.121/) which won an outstanding paper award at EACL 2023 🏆.


##### ▸ NLP for Sensemaking over Large, Specialized Collections

<!-- How can NLP systems help humans identify, organize, and summarize useful information in large document collections? -->

I've published some of the largest gold standard datasets for training and evaluating language models on scientific literature understanding tasks, including [SciTLDR](https://aclanthology.org/2020.findings-emnlp.428/) for summarization, [SciFact](https://aclanthology.org/2020.emnlp-main.609/) for claim verification, [Qasper](https://aclanthology.org/2021.naacl-main.365/) for question answering, and [MultiCite](https://aclanthology.org/2022.naacl-main.137/) for citation discourse understanding.




##### ▸ Designing AI Augmentations for Reading Assistance

<!-- Reading long, technical documents is hard, even for experienced scholars. How can AI assistance help? -->
 <!-- we make them more accessible by automatically transforming papers into dynamic web documents with helpful interactive features?  -->

Since 2020, I have been working on the [Semantic Reader project](https://arxiv.org/abs/2303.14334), which combines HCI and AI to design intelligent reading interfaces for scientists. 
Through this project, I've published work on intelligent reading interfaces such as [ScholarPhi](https://dl.acm.org/doi/10.1145/3411764.3445648) which explains math notation, [Scim](https://dl.acm.org/doi/abs/10.1145/3581641.3584034) which highlights salient passages, and [PaperPlain](https://dl.acm.org/doi/10.1145/3589955) which simplifies difficult passages and provides navigational guidance.
In 2023, my work on [CiteSee](https://dl.acm.org/doi/10.1145/3544548.3580847) on visual augmentation and personalization of inline citations won a best paper award at CHI 🏆.



<!-- I've also worked as a statistician / data scientist in Seattle and an applied probability researcher at [Academia Sinica](https://www.sinica.edu.tw/en) in Taiwan.  I graduated in 2015 with an MS in [Statistics from the University of Washington](https://www.stat.washington.edu/). -->

<!--  Write your biography here. Tell the world about yourself. Link to your favorite [subreddit](http://reddit.com). You can put a picture in, too. The code is already in, just name your picture `prof_pic.jpg` and put it in the `img/` folder. Put your address / P.O. box / other info right below your picture. You can also disable any these elements by editing `profile` property of the YAML header of your `_pages/about.md`. Edit `_bibliography/papers.bib` and Jekyll will render your [publications page](/al-folio/publications/) automatically. Link to your social media connections, too. This theme is set up to use [Font Awesome icons](http://fortawesome.github.io/Font-Awesome/) and [Academicons](https://jpswalsh.github.io/academicons/), like the ones below. Add your Facebook, Twitter, LinkedIn, Google Scholar, or just disable all of them. -->
