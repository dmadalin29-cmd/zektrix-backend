import React, { useState } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Twitter, Facebook, MessageCircle, Link2, Copy, Share2 } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const ShareButton = ({ competitionId, competitionTitle, className }) => {
    const { isRomanian } = useLanguage();
    const [showDialog, setShowDialog] = useState(false);
    const [shareData, setShareData] = useState(null);

    const handleShare = async () => {
        try {
            const response = await axios.get(`${API}/share/competition/${competitionId}`);
            setShareData(response.data);
            setShowDialog(true);
        } catch (error) {
            console.error('Failed to get share data:', error);
            // Fallback to basic share
            setShareData({
                title: competitionTitle,
                share_url: `${window.location.origin}/competitions/${competitionId}`,
                share_text: isRomanian 
                    ? `Participă la competiția "${competitionTitle}" pe Zektrix UK!`
                    : `Enter the "${competitionTitle}" competition on Zektrix UK!`
            });
            setShowDialog(true);
        }
    };

    const copyLink = () => {
        navigator.clipboard.writeText(shareData?.share_url || window.location.href);
        toast.success(isRomanian ? 'Link copiat!' : 'Link copied!');
    };

    const shareOnTwitter = () => {
        const url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareData?.share_text || '')}&url=${encodeURIComponent(shareData?.share_url || '')}`;
        window.open(url, '_blank', 'width=600,height=400');
    };

    const shareOnFacebook = () => {
        const url = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareData?.share_url || '')}`;
        window.open(url, '_blank', 'width=600,height=400');
    };

    const shareOnWhatsApp = () => {
        const url = `https://wa.me/?text=${encodeURIComponent((shareData?.share_text || '') + ' ' + (shareData?.share_url || ''))}`;
        window.open(url, '_blank');
    };

    const nativeShare = async () => {
        if (navigator.share) {
            try {
                await navigator.share({
                    title: shareData?.title,
                    text: shareData?.share_text,
                    url: shareData?.share_url
                });
            } catch (error) {
                if (error.name !== 'AbortError') {
                    console.error('Share failed:', error);
                }
            }
        }
    };

    return (
        <>
            <Button 
                variant="outline" 
                size="sm" 
                onClick={handleShare}
                className={className}
            >
                <Share2 className="w-4 h-4 mr-2" />
                {isRomanian ? 'Distribuie' : 'Share'}
            </Button>

            <Dialog open={showDialog} onOpenChange={setShowDialog}>
                <DialogContent className="sm:max-w-md" aria-describedby="share-dialog-description">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <Share2 className="w-5 h-5 text-primary" />
                            {isRomanian ? 'Distribuie Competiția' : 'Share Competition'}
                        </DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4">
                        <p id="share-dialog-description" className="text-sm text-muted-foreground">
                            {shareData?.share_text}
                        </p>
                        
                        <div className="grid grid-cols-2 gap-3">
                            <Button 
                                onClick={shareOnTwitter}
                                className="bg-[#1DA1F2] hover:bg-[#1DA1F2]/80"
                            >
                                <Twitter className="w-4 h-4 mr-2" />
                                Twitter
                            </Button>
                            <Button 
                                onClick={shareOnFacebook}
                                className="bg-[#4267B2] hover:bg-[#4267B2]/80"
                            >
                                <Facebook className="w-4 h-4 mr-2" />
                                Facebook
                            </Button>
                            <Button 
                                onClick={shareOnWhatsApp}
                                className="bg-[#25D366] hover:bg-[#25D366]/80"
                            >
                                <MessageCircle className="w-4 h-4 mr-2" />
                                WhatsApp
                            </Button>
                            <Button 
                                onClick={copyLink}
                                variant="outline"
                            >
                                <Copy className="w-4 h-4 mr-2" />
                                {isRomanian ? 'Copiază' : 'Copy'}
                            </Button>
                        </div>

                        {navigator.share && (
                            <Button 
                                onClick={nativeShare}
                                variant="outline"
                                className="w-full"
                            >
                                <Link2 className="w-4 h-4 mr-2" />
                                {isRomanian ? 'Mai multe opțiuni...' : 'More options...'}
                            </Button>
                        )}
                    </div>
                </DialogContent>
            </Dialog>
        </>
    );
};

export default ShareButton;
