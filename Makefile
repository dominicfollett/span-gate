local:
	# Start services
	export CLIENT_SECRET=c136879b088b9efcbc9edb604d1b29155f2ac713 && \
	export CLIENT_ID=2ce7e9138650104235dc && \
	python3 main.py --port 8080

clean:
	rm ./lib/aligned-images/cache.*