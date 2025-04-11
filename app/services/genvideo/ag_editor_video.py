import math
import os
import random
from typing import List, Optional
from moviepy import vfx, afx
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.VideoClip import ImageClip, TextClip, VideoClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.fx import CrossFadeIn
from moviepy.video.tools.subtitles import SubtitlesClip


class EditorVideo:
    """
    Agente de Edição de Vídeo que aplica efeitos (zoom, transições, legendas)
    e gera um arquivo final a partir de imagens e áudio.
    """

    def __init__(self, width: int = 480, height: int = 480):
        """
        Inicializa o EditorVideo com dimensões padrão para o vídeo.

        Parâmetros:
            width: Largura padrão do vídeo (padrão: 480).
            height: Altura padrão do vídeo (padrão: 480).
        """
        self.width = width
        self.height = height

    def zoom_in(self, clip: VideoClip, fact: float = 1.2, x_center: float = None, y_center: float = None) -> VideoClip:
        """
        Aplica um efeito de zoom-in dinâmico ao clipe, criando um novo VideoClip com frames modificados.

        Parâmetros:
            clip: Um ImageClip (ou outro clipe estático).
            fact: Fator final de zoom (padrão: 1.2).
            x_center: Coordenada x do ponto central para o zoom.
            y_center: Coordenada y do ponto central para o zoom.
                     Se não informados, escolhe aleatoriamente entre centro e cantos.

        Retorna:
            VideoClip: Novo clipe com o efeito de zoom-in aplicado, redimensionado para self.width x self.height.
        """
        w, h = clip.size
        duration = clip.duration

        # Define ponto central de zoom, se não especificado
        if x_center is None or y_center is None:
            opcoes = [
                (w / 2, h / 2),
                (w / 4, h / 4),
                (3 * w / 4, h / 4),
                (w / 4, 3 * h / 4),
                (3 * w / 4, 3 * h / 4)
            ]
            x_center, y_center = random.choice(opcoes)

        def dynamic_crop_frame(t: float):
            # Calcula o fator de zoom atual (linear de 1 até fact)
            current_factor = 1 + (fact - 1) * (t / duration)
            new_w = w / current_factor
            new_h = h / current_factor

            # Calcula os limites do recorte com base no ponto central
            x1 = max(0, x_center - new_w / 2)
            y1 = max(0, y_center - new_h / 2)
            x2 = min(w, x_center + new_w / 2)
            y2 = min(h, y_center + new_h / 2)

            # Obtém e recorta o frame original
            frame = clip.get_frame(t)
            return frame[int(y1):int(y2), int(x1):int(x2)]

        # Cria um novo VideoClip com o efeito de zoom-in e redimensiona para os valores padrão
        new_clip = VideoClip(frame_function=dynamic_crop_frame, duration=duration)
        return new_clip.resized(width=self.width, height=self.height)

    def crossfade_transition(self, clips: List[VideoClip], transition_duration: float = 3) -> VideoClip:
        """
        Combina uma lista de clipes aplicando uma transição suave de fade cruzado.

        Parâmetros:
            clips: Lista de clipes.
            transition_duration: Duração da transição entre clipes (padrão: 3 segundos).

        Retorna:
            VideoClip: Clipe final com as transições aplicadas.
        """
        new_clips = []
        start_time = 0

        for i, clip in enumerate(clips):
            if i > 0:
                start_time = new_clips[-1].end - transition_duration
            # Define a camada e o tempo de início do clipe
            clip = clip.with_layer_index(0).with_start(start_time)
            # Aplica fade in para clipes após o primeiro
            if i > 0:
                fade_in = CrossFadeIn(transition_duration)
                clip = fade_in.apply(clip)
            new_clips.append(clip)

        final_clip = CompositeVideoClip(new_clips)
        final_clip.duration = new_clips[-1].end
        return final_clip

    def adicionar_legenda(self, video: VideoClip, texto: str, ftname: str = 'assets/fonts/IMPACT.TTF', fontsize: int = 50, color: str = 'white', position=None) -> CompositeVideoClip:
        """
        Adiciona legendas sincronizadas ao vídeo, dividindo o texto em segmentos ao longo da duração do clipe.

        Parâmetros:
            video: O clipe de vídeo original.
            texto: Texto completo da narração.
            ftname: Fonte utilizada (padrão: 'Impact').
            fontsize: Tamanho da fonte (padrão: 36).
            color: Cor do texto.
            position: Posição das legendas no vídeo. Se None, posiciona 20% acima da base.

        Retorna:
            CompositeVideoClip: Clipe com as legendas sobrepostas.
        """
        if position is None:
            position = ("center", video.h * 0.8)

        # Divide o texto em segmentos, utilizando quebras de linha ou pontos
        if "\n" in texto:
            segments = [seg.strip() for seg in texto.split("\n") if seg.strip()]
        else:
            segments = [seg.strip() for seg in texto.split(".") if seg.strip()]

        num_segments = len(segments)
        dur_seg = video.duration / num_segments
        subs = []

        for i, seg in enumerate(segments):
            start = i * dur_seg
            end = start + dur_seg
            subs.append(((start, end), seg))

        def make_txtclip(txt, **kwargs):
            return TextClip(
                text=txt,
                font=ftname,
                font_size=fontsize,
                color="white",
                bg_color=None,
                stroke_color=None,
                stroke_width=0
            ).with_position("center").with_duration(10)

        subtitles = SubtitlesClip(subs, make_textclip=make_txtclip).with_position(position)
        return CompositeVideoClip([video, subtitles])

    def adicionar_titulo(self, video: VideoClip, titulo: str, ftname: str = 'assets/fonts/IMPACT.TTF', fontsize: int = 70, color: str = 'white', position=('center', 'top'), duracao: Optional[float] = None) -> CompositeVideoClip:
        """Adiciona um título ao vídeo."""
        # Se a duração não for especificada, usa a duração do vídeo
        if duracao is None:
            duracao = video.duration

        # Configurações de texto para o título
        titulo_clip = TextClip(
            text=titulo,
            font_size=fontsize,
            color=color,
            font=ftname,
            stroke_color='black',  # Adiciona uma borda preta para legibilidade
            stroke_width=2
        ).with_position(position).with_duration(duracao)

        # Compõe o vídeo original com o título
        video_com_titulo = CompositeVideoClip([video, titulo_clip])
        return video_com_titulo

    def adicionar_marca_dagua(self, video: VideoClip, watermark_path: str,
                              proportion: float = 0.05,  # Proporção da largura do vídeo
                              margin_right: int = 10, margin_top: int = 10,
                              opacity: float = 0.7) -> VideoClip:
        """
        Adiciona uma marca d'água (imagem) no canto superior direito do vídeo,
        redimensionando-a para uma proporção da largura do vídeo.

        :param video:
            Clipe de vídeo original.
        :param watermark_path:
            Caminho para o arquivo de imagem que será usado como marca d'água.
        :param proportion:
            Proporção da largura do vídeo que a marca d'água ocupará (padrão: 0.05, ou seja, 5%).
        :param margin_right:
            Margem (em pixels) da borda direita do vídeo (padrão: 10).
        :param margin_top:
            Margem (em pixels) do topo do vídeo (padrão: 10).
        :param opacity:
            Nível de opacidade (entre 0 e 1) da marca d'água (padrão: 0.7).
        :return:
            Um novo VideoClip com a marca d'água sobreposta.
        """
        # Carrega a imagem da marca d'água
        watermark = ImageClip(watermark_path)

        # Redimensiona a marca d'água para 'proportion' da largura do vídeo, mantendo a proporção
        new_width = video.w * proportion
        watermark = watermark.resized(width=new_width)

        # Ajusta opacidade e duração
        watermark = watermark.with_opacity(opacity).with_duration(video.duration)

        # Define a posição para o canto superior direito, com as margens definidas
        # Observação: a marca d'água precisa ser redimensionada antes de calcular a posição
        def posicao_marca_dagua(clip):
            return (video.w - watermark.w - margin_right, margin_top)

        watermark = watermark.with_position(posicao_marca_dagua)

        # Aplica fade-out de 1 segundo (a partir de video.duration - 1)
        fade_out = vfx.FadeOut(duration=1)
        watermark = watermark.with_effects([fade_out])

        # Cria um CompositeVideoClip para sobrepor a marca d'água ao vídeo
        final_video = CompositeVideoClip([video, watermark])
        return final_video

    def criar_animacao(self, imagens: List[str], audio_path: str = "narracao.mp3",
                       transition_duration: float = 3, legenda_texto: str = None,
                       titulo: str = "Superação",
                       identificador: str = '123') -> str:
        """
        Cria uma animação combinando imagens e áudio, aplicando zoom e transições, e adiciona legendas se fornecidas.

        Parâmetros:
            imagens: Lista de caminhos das imagens.
            audio_path: Caminho para o arquivo de áudio (padrão: "narracao.mp3").
            transition_duration: Duração da transição entre imagens (padrão: 3 segundos).
            legenda_texto: Texto para legendas sincronizadas com o áudio.
            identificador: Identificador para nomear o arquivo de saída (padrão: '123').

        Retorna:
            str: Caminho absoluto do arquivo de vídeo gerado.
        """

        audio = AudioFileClip(audio_path)

        duracao = audio.duration
        num_imgs = len(imagens)
        clip_duration = (duracao + (num_imgs - 1) * transition_duration) / num_imgs
        clips = []

        for img in imagens:
            clip = ImageClip(img).with_duration(clip_duration)
            # Redimensiona a imagem para self.width x self.height
            clip = clip.resized(width=self.width, height=self.height)
            # Aplica o efeito de zoom-in
            clip = self.zoom_in(clip, fact=2)
            clips.append(clip)

        # Aplica transição entre os clipes, se houver mais de um
        video = self.crossfade_transition(clips, transition_duration) if len(clips) > 1 else clips[0]

        video = video.with_duration(duracao).with_audio(audio)

        if legenda_texto:
            video = self.adicionar_legenda(video, legenda_texto)


        video = self.adicionar_titulo(video, titulo=titulo)

        # Usa caminho absoluto para o logo
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'logo.png')
        video = self.adicionar_marca_dagua(video, proportion=0.10, watermark_path=logo_path, opacity=0.5 )

        output = f"{identificador}.mp4"

        video.write_videofile(output, fps=30, codec='libx264', threads=8, preset="fast")

        print(os.path.abspath(output))

        return output

# audio_r = AudioFileClip('teste3.mp3')
# x = EditorVideo()
# a = x.aplicar_efeito_voz_profunda(audio_r, octaves=-0.17)
# a = x.aplicar_reverb_pydub(a, delay_ms=35, decay=0.3, repetitions=6)
# a.write_audiofile('teste3.mp3')


#delay_ms: int = 50,
#decay: float = 0.6,
#repetitions: int = 10) -> AudioFileClip: