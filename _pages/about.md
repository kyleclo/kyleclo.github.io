---
permalink: /
title: "About me"
excerpt: "About me"
author_profile: true
redirect_from: 
  - /about/
  - /about.html
---

I'm a researcher at the Allen Institute for AI on the Semantic Scholar Research team, where I work on NLP and text mining over scientific literature.  Before that, I spent a couple years working as a data scientist in Seattle, and a year as an applied probability researcher at Academia Sinica in Taiwan.  I graduated in 2015 with an MS in Statistics from the University of Washington.


### Research stuff

There's too much scientific literature being published for people to make sense of.  It'd be great if NLP models could improve access to & understanding of the knowledge contained in those papers.  Yet, NLP models that work well on news or Wikipedia articles often perform poorly when applied to scientific text.  I'm interested in understanding why that is & how we can get these systems to perform better.

* Domain adaptation of language models to scientific text improves performance:

  * SciBERT - basically BERT but for scientific text ([code](https://github.com/allenai/scibert)) ([EMNLP 2019 paper](https://www.aclweb.org/anthology/D19-1371/))
  * Don't Stop Pretraining 🎶 your language models ([code](https://github.com/allenai/dont-stop-pretraining)) ([ACL 2020 paper](https://www.aclweb.org/anthology/2020.acl-main.740/)) - 🎉 Runner-up for Best Paper

* We need new challenging scientific tasks & datasets for evaluating these models:

  * Generating short TLDRs that summarize machine learning/AI papers ([demo](https://scitldr.apps.allenai.org/)) ([code](https://github.com/allenai/scitldr)) ([arXiv preprint](https://scitldr.apps.allenai.org/))
  * Scientific fact checking!  Can we verify claims using biomedical papers? ([demo](https://scifact.apps.allenai.org/))  ([code](https://github.com/allenai/scifact)) ([arXiv preprint](https://arxiv.org/abs/2004.14974))
 
* Scientific text is difficult to access (copyright restrictions 😤).  We need large open-access corpora to support scientific NLP research:

  * S2ORC: The Semantic Scholar Open Research Corpus ([download](https://github.com/allenai/s2orc)) ([ACL 2020 talk (12 min)](https://slideslive.com/38929131/s2orc-the-semantic-scholar-open-research-corpus)) ([ACL 2020 paper](https://www.aclweb.org/anthology/2020.acl-main.447/))
  * CORD-19: The COVID-19 Open Research Corpus ([download](https://github.com/allenai/cord19)) ([SIIRH 2020 keynote (18 min)](https://www.youtube.com/watch?v=geX4hSRW2vA)) ([NY-NLP meetup talk (30 min)](https://www.youtube.com/watch?v=GivUfb8KhZY)) ([arXiv preprint](https://arxiv.org/abs/2004.10706)) - Accepted to NLP-COVID workshop at ACL 2020 ([OpenReview](https://openreview.net/forum?id=0gLzHrE_t3z))

* Finally, I'm interested (and concerned) about bias in scientific papers/publishing.  Can we use NLP to study these biases?

  * Quantifying sex bias in clinical trial participation ([JAMA 2019 paper](https://jamanetwork.com/journals/jamanetworkopen/fullarticle/2737103))


### Community stuff

It'd be great if more researchers in the NLP & text mining communities worked on scientific text.  To promote this, I've co-organized workshops & shared tasks:

* Shared tasks

  * TREC-COVID - Information retrieval challenge over an evolving CORD-19 corpus ([link](https://ir.nist.gov/covidSubmit/)) ([JAMIA 2020 paper](https://academic.oup.com/jamia/article/doi/10.1093/jamia/ocaa091/5828938)) ([SIGIR Forum 2020 paper](http://www.sigir.org/wp-content/uploads/2020/06/p03.pdf))

* Workshops

  * 1st SciNLP workshop at AKBC 2020  ([link](http://scinlp.org/)) ([recorded talks](https://www.youtube.com/playlist?list=PLOTELVgUs9jKW2EkJbAyi6DcunfaXf0r6))


### My collaborators

All of my projects has been collaborations with other awesome researchers.  Many thanks to:  

[Waleed Ammar (Google)](https://wammar.github.io/), [Iz Beltagy (AI2)](https://beltagy.net/), [Isabel Cachola (AI2)](https://isabelcachola.com/), [Arman Cohan (AI2)](https://armancohan.com/), [Sergey Feldman (AI2)](https://www.data-cowboys.com/team), [Suchin Gururangan (UW/AI2)](https://suchin.io/), [Rodney Kinney (AI2)](https://www.linkedin.com/in/rodney-kinney-503926), [Ana Marasović (UW/AI2)](https://www.anamarasovic.com/), [Mark Neumann (AI2)](http://markneumann.xyz/), [Swabha Swayamdipta (UW/AI2)](https://swabhs.com/), [Dave Wadden (UW)](https://github.com/dwadden), [Lucy Lu Wang (AI2)](https://llwang.net/).
