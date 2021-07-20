---
permalink: /
title: "About me"
excerpt: "About me"
author_profile: true
redirect_from: 
  - /about/
  - /about.html
---

I'm a researcher at the [Allen Institute for AI](https://allenai.org/) on the [Semantic Scholar Research team](https://research.semanticscholar.org/).  Before that, I worked as a statistician in Seattle and research assistant in the Applied Probability group at [Academia Sinica](https://www.sinica.edu.tw/en) in Taiwan.  I graduated in 2015 with an MS in [Statistics from the University of Washington](https://www.stat.washington.edu/).


# Research

I build tools that help scientists do science 🔬, so my research interests cover NLP, ML and HCI.  Areas I'm mainly interested in:

* [**Language modeling**](#language-modeling) for scientific text
* [**Summarization**](#summarization) of scientific papers
* [**Fact checking**](#fact-checking) claims about scientific phenomena using published literature
* ✨[**Question answering**](#question-answering) over scientific papers
* ✨[**Information extraction**](#information-extraction) of structured knowledge from scientific papers
* [**Corpora and resources**](#corpora-and-resources) to support other researchers interested in NLP for scientific text
* [**Augmented reading**](#augmented-reading) of scientific papers to improve comprehension


I've also done some work in:

* ✨[**Few shot learning**](#few-shot-learning)
* [**Generation**](#generation)
* [**Explainable AI**](#explainable-ai)
* ✨[**Science of science**](#science-of-science)


### Language modeling 

  * *Don't Stop Pretraining 🎶: Adapt language models to domains and tasks* ([ACL 2020](https://www.aclweb.org/anthology/2020.acl-main.740/)) ([GitHub](https://github.com/allenai/dont-stop-pretraining))  - 🎉 Runner-up for Best Paper
<!--    * [ACL 2020 talk (11 min) by Suchin](https://slideslive.com/38929123/dont-stop-pretraining-adapt-language-models-to-domains-and-tasks) -->
<!--    * [video (15 min) by Henry AI Labs](https://www.youtube.com/watch?v=zNjiTcF3FZE) -->
  * *SciBERT: A pretrained language model for scientific text* ([EMNLP 2019](https://www.aclweb.org/anthology/D19-1371/)) ([GitHub](https://github.com/allenai/scibert))

### Summarization

  * *TLDR: Extreme summarization of scientific documents* ([EMNLP 2020 - Findings](https://www.aclweb.org/anthology/2020.findings-emnlp.428/))  ([GitHub](https://github.com/allenai/scitldr)) 
    * See live in production on [Semantic Scholar](https://tldr.semanticscholar.org/)
    * In the news: [Nature](https://www.nature.com/articles/d41586-020-03277-2), [MIT Tech Review](https://www.technologyreview.com/2020/11/18/1012259/ai-summarizes-science-papers-ai2-semantic-scholar/), [TNW](https://thenextweb.com/neural/2020/11/20/tldr-this-ai-summarizes-research-papers-so-you-dont-have-to/)

<!--    * [video (12 min) by Henry AI Labs](https://www.youtube.com/watch?v=5WJZgSwRUSQ) -->

### Fact checking

  * *SciFact: Scientific claim verification* ([EMNLP 2020](https://www.aclweb.org/anthology/2020.emnlp-main.609/)) ([GitHub](https://github.com/allenai/scifact)) 
    * Follow progress on our [public leaderboard](https://leaderboard.allenai.org/scifact/submissions/public) and [live demo](https://scifact.apps.allenai.org/)
    * In the news: [MIT Tech Review](https://www.technologyreview.com/2020/05/29/1002349/ai-coronavirus-scientific-fact-checking/), [VentureBeat](https://venturebeat.com/2020/05/04/allen-institutes-verisci-uses-ai-to-fact-check-scientific-claims/), [ZDNet](https://www.zdnet.com/article/scientific-fact-checking-using-ai-language-models-covid19-research-and-beyond/)
 
### Question answering

  * ✨New paper✨ *Qasper: Information-seeking QA over research papers* ([NAACL 2021](https://aclanthology.org/2021.naacl-main.365/)) ([GitHub](https://github.com/allenai/qasper-led-baseline)) 
 
### Information extraction

  * ✨New preprint✨ *VILA: Incorporating visual layout for scientific PDF parsing* ([arXiv 2021](https://arxiv.org/abs/2106.00676)) ([GitHub](https://github.com/allenai/vila))
  * *Document-Level definition detection in scholarly documents* ([SDP at EMNLP 2020](https://www.aclweb.org/anthology/2020.sdp-1.22/))
  * *Combining distant and direct supervision for neural relation extraction* ([NAACL 2019](https://www.aclweb.org/anthology/N19-1184/))
  * *Construction of the literature graph in Semantic Scholar* ([NAACL 2018](https://www.aclweb.org/anthology/N18-3011/))

### Corpora and resources

  * *S2ORC: The Semantic Scholar Open Research Corpus* ([ACL 2020](https://www.aclweb.org/anthology/2020.acl-main.447/)) ([GitHub](https://github.com/allenai/s2orc))
    * *s2orc-doc2json* for parsing PDFs and LaTeX to JSON format ([GitHub](https://github.com/allenai/s2orc-doc2json))
<!--     * [ACL 2020 talk (12 min)](https://slideslive.com/38929131/s2orc-the-semantic-scholar-open-research-corpus) -->
    
  * *CORD-19: The COVID-19 Open Research Corpus* ([NLP-COVID at ACL 2020](https://www.aclweb.org/anthology/2020.nlpcovid19-acl.1/)) ([OpenReview](https://openreview.net/forum?id=0gLzHrE_t3z)) ([GitHub](https://github.com/allenai/cord19))
    * [SIIRH 2020 at ECIR 2020 keynote (18 min)](https://www.youtube.com/watch?v=geX4hSRW2vA) (April 14, 2020)
    * [AWS Education: Research Seminar talk (60 min)](https://www.youtube.com/watch?v=qjv8MLJVbZw&feature=youtu.be) (July 29, 2020)
    * In the news: [White House OSTP](https://www.whitehouse.gov/briefings-statements/call-action-tech-community-new-machine-readable-covid-19-dataset/), [Science](https://www.sciencemag.org/news/2020/05/scientists-are-drowning-covid-19-papers-can-new-tools-keep-them-afloat), [Nature](https://www.nature.com/articles/d41586-020-01733-7), [TechCrunch](https://techcrunch.com/2020/03/16/coronavirus-machine-learning-cord-19-chan-zuckerberg-ostp/), Geekwire [[1]](https://www.geekwire.com/2020/ai2-microsoft-team-tech-leaders-use-ai-war-coronavirus/) [[2]](https://www.geekwire.com/2020/software-tools-mining-covid-19-research-studies-go-viral-among-scientists/)

<!--    * [NY-NLP meetup talk (30 min)](https://www.youtube.com/watch?v=GivUfb8KhZY) (April 27, 2020) -->

### Augmented reading

  * *ScholarPhi: Just-in-Time, Position-Sensitive Definitions of Terms and Symbols* ([CHI 2021](https://arxiv.org/abs/2009.14237))
    * Try our [live demo](http://chi2021demo.scholarphi.org/)

### Few shot learning

  * ✨New preprint✨ *FLEX: Unifying Evaluation for Few-Shot NLP* ([arXiv 2021; under submission](https://arxiv.org/abs/2107.07170))

### Generation

  * *Citation text generation* ([arXiv 2020; under submission](https://arxiv.org/abs/2002.00317))

### Explainable AI

  * *Explanation-based tuning of opaque machine learners* ([arXiv 2020; under submission](https://arxiv.org/abs/2003.04315))

### Science of science

  * ✨New preprint✨ *MultiCite: Moving beyond the single-sentence single-label setting* ([arXiv 2021](https://arxiv.org/abs/2107.00414)) ([GitHub](https://github.com/allenai/multicite))
  * *Text mining approaches for dealing with the rapidly expanding literature on COVID-19* ([Briefings in Bioinformatics 2020](https://academic.oup.com/bib/advance-article/doi/10.1093/bib/bbaa296/6024738))
  * *Quantifying sex bias in clinical trial participation* ([JAMA 2019](https://jamanetwork.com/journals/jamanetworkopen/fullarticle/2737103))
    * In the news: [Quartz article](https://qz.com/1657408/why-are-women-still-underrepresented-in-clinical-research/)
  * *Citation count analysis for papers with preprints* ([arXiv 2018](https://arxiv.org/abs/1805.05238))

# Shared tasks

  * SciVER at SDP 2021 (NAACL 2021) - Scientific claim verification ([link](https://sdproc.org/2021/sharedtasks.html#sciver))
  * EPIC-QA at TAC 2020 - Open domain question answering challenge: Can systems handle a mixture of questions from *experts* as well as *consumers*? ([link](https://bionlp.nlm.nih.gov/epic_qa/))
  * TREC-COVID at TREC 2020 - Information retrieval challenge over an evolving CORD-19 corpus ([link](https://ir.nist.gov/covidSubmit/)) ([JAMIA 2020 paper](https://academic.oup.com/jamia/article/doi/10.1093/jamia/ocaa091/5828938)) ([SIGIR Forum 2020 paper](http://www.sigir.org/wp-content/uploads/2020/06/p03.pdf))

# Workshops

  * The 2nd SDP workshop will be at NAACL 2021! Stay tuned! ([link](http://sdproc.org/2021/))

  * 1st SciNLP workshop at AKBC 2020  ([link](http://scinlp.org/)) ([recorded talks](https://www.youtube.com/playlist?list=PLOTELVgUs9jKW2EkJbAyi6DcunfaXf0r6)) - What a success!  166 of 422 AKBC attendees signed up for our workshop!  Stay tuned for the next one ;)


# My collaborators

My projects have been collaborations with other awesome researchers ❤️.  Many thanks to:

[Waleed Ammar (Google)](https://wammar.github.io/), [Iz Beltagy (AI2)](https://beltagy.net/), [Isabel Cachola (JHU)](https://isabelcachola.com/), [Arman Cohan (AI2)](https://armancohan.com/), [Doug Downey (AI2/Northwestern)](https://users.cs.northwestern.edu/~ddowney/), [Sergey Feldman (AI2)](https://www.data-cowboys.com/team), [Suchin Gururangan (UW/AI2)](https://suchin.io/), [Andrew Head (UC Berkeley/AI2/U Penn)](https://andrewhead.info/), [Dongyeop Kang (UC Berkeley/U. Minnesota)](https://dykang.github.io/), [Rodney Kinney (AI2)](https://www.linkedin.com/in/rodney-kinney-503926), [Ben Lee (UW)](https://bcglee.github.io/), [Ana Marasović (UW/AI2)](https://www.anamarasovic.com/), [Mark Neumann (AI2)](http://markneumann.xyz/), [Shannon Shen (AI2)](https://szj.io/), [Swabha Swayamdipta (UW/AI2)](https://swabhs.com/), [Dave Wadden (UW)](https://github.com/dwadden), [Lucy Lu Wang (AI2)](https://llwang.net/).
