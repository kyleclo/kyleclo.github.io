---
permalink: /
title: "About me"
excerpt: "About me"
author_profile: true
redirect_from: 
  - /about/
  - /about.html
---

I'm a researcher at the [Allen Institute for AI](https://allenai.org/) on the [Semantic Scholar Research team](https://research.semanticscholar.org/), where I work on NLP and text mining over scientific literature.  Before that, I spent a couple years working as a data scientist in Seattle, and a year as an applied probability researcher at [Academia Sinica](https://www.sinica.edu.tw/en) in Taiwan.  I graduated in 2015 with an MS in [Statistics from the University of Washington](https://www.stat.washington.edu/).


# Research stuff

There's too much scientific literature being published for people to make sense of.  It'd be great if NLP models could improve access to & understanding of the knowledge contained in those papers.  Yet, NLP models that work well on news or Wikipedia articles often perform poorly when applied to scientific text.  I'm interested in understanding why that is & how we can get these systems to perform better.

### Language modeling for science

One of the best ways to improve performance on many scientific NLP tasks is to adapt the underlying language models to the scientific domain:

  * SciBERT - basically BERT but for scientific text ([code](https://github.com/allenai/scibert)) ([EMNLP 2019 paper](https://www.aclweb.org/anthology/D19-1371/))
  * Don't Stop Pretraining 🎶 your language models ([code](https://github.com/allenai/dont-stop-pretraining)) ([ACL 2020 talk (11 min)](https://slideslive.com/38929123/dont-stop-pretraining-adapt-language-models-to-domains-and-tasks)) ([ACL 2020 paper](https://www.aclweb.org/anthology/2020.acl-main.740/)) - 🎉 Runner-up for Best Paper
    * [video (15 min) by Henry AI Labs](https://www.youtube.com/watch?v=zNjiTcF3FZE)

### Scientific NLP tasks & datasets

We need new challenging scientific tasks & datasets for evaluating these models:

  * Generating short TLDRs that summarize machine learning/AI papers ([demo](https://scitldr.apps.allenai.org/)) ([code](https://github.com/allenai/scitldr)) ([arXiv preprint](https://scitldr.apps.allenai.org/)) 
    * [video (12 min) by Henry AI Labs](https://www.youtube.com/watch?v=5WJZgSwRUSQ)
    
  * Scientific fact checking!  Can we verify claims using biomedical papers? ([demo](https://scifact.apps.allenai.org/))  ([code](https://github.com/allenai/scifact)) ([arXiv preprint](https://arxiv.org/abs/2004.14974)) 
    * In the news: [MIT Tech Review](https://www.technologyreview.com/2020/05/29/1002349/ai-coronavirus-scientific-fact-checking/), [VentureBeat](https://venturebeat.com/2020/05/04/allen-institutes-verisci-uses-ai-to-fact-check-scientific-claims/), [ZDNet](https://www.zdnet.com/article/scientific-fact-checking-using-ai-language-models-covid19-research-and-beyond/)
 
### Resources for scientific NLP

Scientific text is difficult to access (copyright restrictions 😤).  We need large, machine-readable, open-access corpora to support scientific NLP research:

  * S2ORC: The Semantic Scholar Open Research Corpus ([download](https://github.com/allenai/s2orc)) ([ACL 2020 paper](https://www.aclweb.org/anthology/2020.acl-main.447/))
    * [ACL 2020 talk (12 min)](https://slideslive.com/38929131/s2orc-the-semantic-scholar-open-research-corpus)
  * CORD-19: The COVID-19 Open Research Corpus ([download](https://github.com/allenai/cord19))([arXiv preprint](https://arxiv.org/abs/2004.10706)) - Accepted to NLP-COVID at ACL 2020 ([OpenReview](https://openreview.net/forum?id=0gLzHrE_t3z))
    * [SIIRH 2020 at ECIR 2020 keynote (18 min)](https://www.youtube.com/watch?v=geX4hSRW2vA) (April 14, 2020)
    * [NY-NLP meetup talk (30 min)](https://www.youtube.com/watch?v=GivUfb8KhZY) (April 27, 2020)
    * [AWS Education: Research Seminar talk (60 min)](https://www.youtube.com/watch?v=qjv8MLJVbZw&feature=youtu.be) (July 29, 2020)
    * In the news: [White House OSTP](https://www.whitehouse.gov/briefings-statements/call-action-tech-community-new-machine-readable-covid-19-dataset/), [Science](https://www.sciencemag.org/news/2020/05/scientists-are-drowning-covid-19-papers-can-new-tools-keep-them-afloat), [Nature](https://www.nature.com/articles/d41586-020-01733-7), [TechCrunch](https://techcrunch.com/2020/03/16/coronavirus-machine-learning-cord-19-chan-zuckerberg-ostp/), Geekwire [[1]](https://www.geekwire.com/2020/ai2-microsoft-team-tech-leaders-use-ai-war-coronavirus/) [[2]](https://www.geekwire.com/2020/software-tools-mining-covid-19-research-studies-go-viral-among-scientists/)

### Tools that make research less painful

  * arXiv paper recommender w/ actionable explanations ([link](https://s2-sanity.apps.allenai.org)) ([arXiv preprint](https://arxiv.org/abs/2003.04315))
    * Adopted into production. Live on [Semantic Scholar](https://www.semanticscholar.org/feed/create)


### Science of science

I'm interested (and concerned) about bias in scientific papers/publishing.  Can we use NLP to study these biases?

  * Quantifying sex bias in clinical trial participation ([JAMA 2019 paper](https://jamanetwork.com/journals/jamanetworkopen/fullarticle/2737103))
    * In the news: [Quartz](https://qz.com/1657408/why-are-women-still-underrepresented-in-clinical-research/)


# Community stuff

It'd be great if more researchers in the NLP & text mining communities worked on scientific text.  To promote this, I've co-organized workshops & shared tasks:

* Shared tasks

  * TREC-COVID - Information retrieval challenge over an evolving CORD-19 corpus ([link](https://ir.nist.gov/covidSubmit/)) ([JAMIA 2020 paper](https://academic.oup.com/jamia/article/doi/10.1093/jamia/ocaa091/5828938)) ([SIGIR Forum 2020 paper](http://www.sigir.org/wp-content/uploads/2020/06/p03.pdf))

* Workshops

  * 1st SciNLP workshop at AKBC 2020  ([link](http://scinlp.org/)) ([recorded talks](https://www.youtube.com/playlist?list=PLOTELVgUs9jKW2EkJbAyi6DcunfaXf0r6))


# My collaborators

All of my projects have been collaborations with other awesome researchers.  Many thanks to:  

[Waleed Ammar (Google)](https://wammar.github.io/), [Iz Beltagy (AI2)](https://beltagy.net/), [Isabel Cachola (AI2)](https://isabelcachola.com/), [Arman Cohan (AI2)](https://armancohan.com/), [Doug Downey (AI2/Northwestern)](https://users.cs.northwestern.edu/~ddowney/), [Sergey Feldman (AI2)](https://www.data-cowboys.com/team), [Suchin Gururangan (UW/AI2)](https://suchin.io/), [Rodney Kinney (AI2)](https://www.linkedin.com/in/rodney-kinney-503926), [Ben Lee (UW)](https://bcglee.github.io/), [Ana Marasović (UW/AI2)](https://www.anamarasovic.com/), [Mark Neumann (AI2)](http://markneumann.xyz/), [Swabha Swayamdipta (UW/AI2)](https://swabhs.com/), [Dave Wadden (UW)](https://github.com/dwadden), [Lucy Lu Wang (AI2)](https://llwang.net/).
