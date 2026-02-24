.PHONY: help build serve check-links check-links-docker check-links-external clean docker-up docker-down generate-cv

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build the Jekyll site locally
	bundle exec jekyll build

serve: ## Serve the Jekyll site locally with live reload
	bundle exec jekyll serve --watch --port=8080 --host=0.0.0.0 --livereload --verbose

check-links: build ## Build site and check for broken links (requires lychee installed)
	@./scripts/check_links.sh

check-links-docker: ## Check for broken links using Docker
	@echo "Building Jekyll site with Docker..."
	docker compose run --rm jekyll bundle exec jekyll build
	@echo "Checking links with lychee..."
	docker compose run --rm link-checker

check-links-external: ## Check all links including external URLs using Docker
	docker compose run --rm link-checker-external

docker-up: ## Start Jekyll development server with Docker
	docker compose up

docker-down: ## Stop Docker containers
	docker compose down

docker-build: ## Build site using Docker (without starting server)
	docker compose run --rm jekyll bundle exec jekyll build

clean: ## Clean generated site files
	bundle exec jekyll clean
	rm -rf _site .jekyll-cache .jekyll-metadata

install: ## Install dependencies
	bundle install

generate-cv: ## Generate publications.tex and push to Overleaf CV
	python scripts/generate_cv.py
