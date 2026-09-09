require 'json'

module Jekyll
  class KinderPageGenerator < Generator
    safe true
    priority :normal

    def generate(site)
      kinders = load_json(site, '_rawdata/kinder.json')

      Jekyll.logger.info "KinderGenerator:", "#{kinders.size}개 유치원 페이지 생성 중..."
      kinders.each do |k|
        next if k['slug'].to_s.strip.empty?
        site.pages << KinderPage.new(site, k)
      end

      Jekyll.logger.info "KinderGenerator:", "완료 (#{kinders.size}개)"
    end

    private

    def load_json(site, path)
      file = File.join(site.source, path)
      return [] unless File.exist?(file)
      JSON.parse(File.read(file, encoding: 'utf-8'))
    rescue => e
      Jekyll.logger.warn "KinderGenerator:", "#{path} 로드 실패: #{e.message}"
      []
    end
  end

  class KinderPage < Page
    def initialize(site, k)
      @site = site
      @base = site.source
      @dir  = "kinder/#{k['slug']}"
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(@base, '_layouts'), 'kinder.html')
      self.data.merge!(k)
      self.data['layout']      = 'kinder'
      self.data['title']       = build_title(k)
      self.data['description'] = build_desc(k)
    end

    private

    def build_title(k)
      loc = [k['sido_nm'], k['sggu_nm']].compact.join(' ')
      "#{k['kinderName']} #{loc} 위치·전화번호·학급정보"
    end

    def build_desc(k)
      loc = [k['sido_nm'], k['sggu_nm']].compact.join(' ')
      "#{loc} #{k['kinderName']}(#{k['foundType']})의 주소, 전화번호, 운영시간, 학급수·원아정원 정보를 확인하세요."[0, 155]
    end
  end
end
